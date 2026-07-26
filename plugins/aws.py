from typing import List, Literal

import awswrangler as wr
import boto3
import pandas as pd


def get_s3_client():
    """
    Create, initializes and return an Amazon S3 client using boto3.
    """
    return boto3.client("s3")


def get_ssm_parameter(ssm_parameter_name: str):
    """Fetch the value of a parameter from AWS Systems Manager Parameter Store
    Args:
        ssm_parameter_name (str): The name of the parameter to fetch.
    Returns:
        str: The value of the specified parameter.
    """
    client = boto3.client('ssm', region_name='eu-central-1',)
    response = client.get_parameter(Name=ssm_parameter_name,
                                    WithDecryption=True)
    ssm_params_value = response['Parameter']['Value']
    return ssm_params_value


def list_objects(bucket: str, prefix: str) -> List:
    """List S3 object keys matching a bucket and prefix.

    Args:
        bucket: Name of the S3 bucket to search
        prefix: Key prefix to filter objects by.

    Returns:
        A list of matching S3 object keys.
    """
    keys = wr.s3.list_objects(f's3://{bucket}/{prefix}')
    return keys


def write_partitions(
    data: pd.DataFrame,
    dest_bucket: str,
    partition_cols: List,
    write_mode: Literal["append", "overwrite"] | None,
    dataset: bool = True,
) -> List[str]:
    """Write a DataFrame to S3 as a Hive-partitioned Parquet dataset.

    Uses awswrangler to write the DataFrame to a given  bucket,
    partitioning by the specified columns.

    Args:
        data: The DataFrame to write.
        dest_bucket: Name of the destination S3 bucket
        partition_cols: Column names to partition the dataset by.
        write_mode: Write mode to use.
        dataset: Whether to write as a partitioned dataset or as a
            single file. Defaults to True.

    Returns:
        output_paths: List of S3 URIs for all files written.

    Raises:
        Exception: If `write_mode` is not "append" or "overwrite".
    """
    if write_mode not in ['append', 'overwrite']:
        raise Exception(f'mode {write_mode} is not supported.')

    destination = f"s3://{dest_bucket}"
    result = wr.s3.to_parquet(
        df=data,
        path=destination,
        dataset=dataset,
        partition_cols=partition_cols,
        mode=write_mode
    )
    output_paths = result["paths"]
    return output_paths
