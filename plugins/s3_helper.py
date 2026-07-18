import json
import logging

import awswrangler as wr
import boto3
import pandas as pd

logger = logging.getLogger(__name__)


def get_latest_s3_file(bucket: str, prefix: str):
    """
    Return the latest file in an S3 prefix.
    """
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{prefix}/")
    files = response.get("Contents", [])

    if not files:
        raise ValueError(f"No files found in s3://{bucket}/{prefix}")

    logger.info(f"{len(files)} file(s) found in s3://{bucket}/{prefix}")

    latest_object = max(files, key=lambda x: x["LastModified"])

    latest_file_path = f"s3://{bucket}/{latest_object['Key']}"

    logger.info(f"Latest file: {latest_file_path}")

    return latest_file_path


def read_latest_data_from_s3(bucket: str, prefix: str):
    """
    Read the latest Parquet file from S3.
    """
    logger.info("Getting latest file.")

    full_path = get_latest_s3_file(bucket, prefix)

    df = wr.s3.read_parquet(full_path)

    if df.empty:
        raise ValueError(f"No data found in {full_path}")

    logger.info(f"Getting latest data from {full_path}.")

    return df


def write_df_to_s3(
    df,
    bucket_name,
    folder_name,
    file_name,
    dataset=False,
):
    """
    Write a DataFrame to S3 as a Parquet file.
    """
    s3_path = f"s3://{bucket_name}/{folder_name}/{file_name}"

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=dataset,
    )

    return f"Data successfully written to {s3_path}"


def write_dataframe_to_s3_glue(
    df: pd.DataFrame,
    path: str,
    filename_prefix: str,
    partition_cols: list[str] = None,
    database: str | None = None,
    table: str | None = None,
    mode: str = "append",
) -> None:
    """
    Write a DataFrame to S3 and optionally register it in Glue.
    """
    logger.info(f"Writing DataFrame to S3 at {path} with mode={mode}")

    wr.s3.to_parquet(
        df=df,
        path=path,
        dataset=True,
        mode=mode,
        partition_cols=partition_cols,
        database=database,
        table=table,
        filename_prefix=filename_prefix,
    )

    logger.info("Write to S3 completed successfully.")


def write_json(
    data: dict,
    bucket_name: str,
    object_key: str,
) -> str:
    """
    Write a JSON object to S3.
    """
    s3 = boto3.client("s3")

    s3.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json.dumps(data),
        ContentType="application/json",
    )

    s3_path = f"s3://{bucket_name}/{object_key}"

    logger.info(f"JSON written to {s3_path}")

    return s3_path


def read_json(
    bucket_name: str,
    object_key: str,
) -> dict:
    """
    Read a JSON object from S3.
    """
    s3 = boto3.client("s3")

    response = s3.get_object(
        Bucket=bucket_name,
        Key=object_key,
    )

    return json.loads(response["Body"].read().decode("utf-8"))
