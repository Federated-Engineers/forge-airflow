import json
from typing import Dict, List, Tuple

import awswrangler as wr
import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from plugins.aws import list_keys
from plugins.logger import log

config = Variable.get("BALTILOGIX", deserialize_json=True)
s3_hook = S3Hook()


def find_files() -> List | None:
    """Find S3 object keys for the configured BaltiLogix source bucket/path.

    Reads the source bucket and path, lists matching keys, and raises
    an error if none are found.

    Returns:
        A list of matching S3 object keys.

    Raises:
        Exception: If no files are found at the configured S3 location.
    """
    src_bucket, src_path = (
        config.get("BALTILOGIX_SOURCE"),
        config.get("BALTILOGIX_PATH")
    )
    keys = list_keys(s3_hook, src_bucket, src_path)

    if not keys:
        raise Exception(
            f"Could not find any files in "
            f"s3://{src_bucket}/{src_path}"
        )
    log.info(f"Found {keys} files in {src_path}")

    return keys


def process_and_count_objects(keys: List) -> Tuple[pd.DataFrame, int]:
    """Read a list of JSON objects into DataFrames and combine them.

    Each key is read via pandas' JSON reader and the resulting DataFrames
    are concatenated into a single combined DataFrame.

    Args:
        keys: A list of S3 keys pointing to JSON objects to read.

    Returns:
        A tuple of:
            - The combined DataFrame from all read objects.
            - The total row count of the combined DataFrame.
    """
    src_bucket = config.get("BALTILOGIX_SOURCE")
    stack = []

    for key in keys:
        log.info(f"Processing {key}")
        content = s3_hook.read_key(key=key, bucket_name=src_bucket)
        content = json.loads(content)
        data = pd.json_normalize(content)
        stack.append(data)

    final_stack = pd.concat(stack, ignore_index=True)
    object_count = len(final_stack)

    return final_stack, object_count


def write_partitions(data: pd.DataFrame) -> List[str]:
    """Write a DataFrame to S3 as a Hive-partitioned Parquet dataset.

    Writes the given DataFrame to the configured destination bucket using
        AWS Data Wrangler, partitioning by timestamp and overwriting only the
        affected partitions.

        Args:
            data: The DataFrame to write.

        Returns:
            output_paths: The list of strings containing the S3
            locations of all the files created.
    """
    dest_bucket = config.get("BALTILOGIX_DEST")
    dest_path = f"s3://{dest_bucket}"
    result = wr.s3.to_parquet(
        df=data,
        path=dest_path,
        dataset=True,


        partition_cols=["vin"],   # test
        mode="append"
    )
    output_paths = result["paths"]
    return output_paths


def run_compaction() -> Dict:
    """Run the IoT telemetry compaction pipeline.

    Finds source JSON files in S3, reads and combines them into a single
    DataFrame, and writes the result out as partitioned Parquet.

    Returns:
        A tuple of:
            - input_count: Number of input rows read from source files.
            - output_paths: list of strings containing the S3
                    locations of all the written files.
    """

    files = find_files()
    data, source_count = process_and_count_objects(files)
    output_paths = write_partitions(data)

    return {"source_count": source_count, "output_paths": output_paths}


def validate_output(source_count: int, output_paths: List) -> None:
    """Validate output Parquet files after compaction.

    Checks each file's schema, that key columns (timestamp) contain no
    nulls, and that the total number of records read matches
    the number written.

    Args:
        source_count: Number of records read from source files.
        output_paths: List of S3 paths to the written Parquet files.

    Raises:
        Exception: If any file's schema doesn't match expectations, if
            timestamp contains nulls, or if source_count and written_count
            don't match.
    """
    expected_columns = config.get("EXPECTED_COLUMNS")
    written_count = 0

    for path in output_paths:
        output = pd.read_parquet(path)

        if set(output.columns) != set(expected_columns):
            raise Exception(
                f"schema mismatch: expected columns {expected_columns}, "
                f"got {set(output.columns)} at {path}"
            )

        if output["timestamp"].isna().any():
            raise Exception(f"null values found in timestamp column at {path}")

        written_count += len(output)

    if source_count != written_count:
        raise Exception(
            f"Read {source_count} records but wrote "
            f"{written_count}"
        )
