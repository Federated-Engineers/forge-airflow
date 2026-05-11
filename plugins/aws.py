import base64
import json
from io import BytesIO
from typing import Dict, List

import awswrangler as wr
import boto3
import pandas as pd
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from plugins.logger import log

s3_hook = S3Hook()


def retrieve_ssm_parameter_value() -> Dict | str:
    """
    Retrieve Google service account credentials from
    AWS Systems Manager Parameter Store.

    Returns:
        Dict | str: Parsed credentials dict, or raw string if not JSON

    Raises:
        ValueError: If the parameter value cannot be parsed
    """
    client = boto3.session.Session().client(service_name="ssm")
    response = client.get_parameter(
        Name="/production/google-service-account/credentials",
        WithDecryption=True
    )
    value = response["Parameter"]["Value"]

    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError) as e:
        log.info(f"Could not parse SSM parameter as JSON. ERROR {str(e)}")
        pass

    try:
        decoded = base64.b64decode(value).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        log.info(
            f"Could not parse SSM parameter as base64-encoded JSON. "
            f"ERROR {str(e)}"
        )
        pass

    return value


def copy_data_from_s3(bucket_name: str, object_key: str) -> bytes:
    """Read an object from S3 and return its contents.

    Args:
        bucket_name: Name of the source S3 bucket.
        object_key: Key of the object to read.

    Returns:
        Raw file contents as bytes.
    """
    # log.info(f"Reading from s3://{bucket_name}/{object_key}")
    # #this one makes th logs quite noisy not sure if I should keep it.
    return s3_hook.read_key(key=object_key, bucket_name=bucket_name)


def load_data_to_s3(
        buffer: BytesIO,
        hook: S3Hook,
        dest_bucket: str,
        dest_key: str
        ) -> None:

    hook.load_file_obj(
        file_obj=buffer,
        key=dest_key,
        bucket_name=dest_bucket,
        replace=True
    )


def write_to_s3_for_glue(
        df: pd.DataFrame,
        bucket: str,
        s3_prefix: str,
        database: str,
        glue_table: str,
        partition_cols: List[str]
):
    wr.s3.to_parquet(
        df=df,
        path=f"s3://{bucket}/{s3_prefix}/",
        dataset=True,
        database=database,
        table=glue_table,
        partition_cols=partition_cols or [],
        mode="append",
        schema_evolution=True
    )
