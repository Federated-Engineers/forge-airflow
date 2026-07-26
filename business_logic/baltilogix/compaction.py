import json
from typing import Dict, List, Tuple

import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from plugins.aws import list_objects, write_partitions
from plugins.logger import log

config = Variable.get("BALTILOGIX", deserialize_json=True)
s3_hook = S3Hook()


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
        parsed_key = "/".join(key.replace("s3://", "").split("/")[1:])

        content = s3_hook.read_key(key=parsed_key, bucket_name=src_bucket)
        content = json.loads(content)
        df = pd.json_normalize(content)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        df["year"] = df["timestamp"].dt.year
        df["month"] = df["timestamp"].dt.month
        df["day"] = df["timestamp"].dt.day
        stack.append(df)

    final_stack = pd.concat(stack, ignore_index=True)
    object_count = len(final_stack)

    return final_stack, object_count


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

    src_bucket, src_prefix, dest_bucket = (
        config.get("BALTILOGIX_SOURCE"),
        config.get("BALTILOGIX_PATH"),
        config.get("BALTILOGIX_BUCKET")
    )
    files = list_objects(src_bucket, src_prefix)
    data, source_count = process_and_count_objects(files)
    partition_columns = ["year", "month", "day", "vehicle_type"]

    output_paths = write_partitions(
        data,
        dest_bucket,
        partition_columns,
        "overwrite"
    )

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
