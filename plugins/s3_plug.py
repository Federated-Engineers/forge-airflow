import logging

import boto3

log = logging.getLogger(__name__)


def get_s3_files_sorted(bucket: str, folder: str):
    """
    Retrieve ALL file paths from S3 bucket/folder sorted by LastModified.

    This is the foundation for:
    - incremental ETL
    - backfill processing
    - replay-safe pipelines
    """
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{folder}/")
    files = response.get("Contents", [])
    if not files:
        raise ValueError(f"No files found in s3://{bucket}/{folder}/")

    log.info(f"Found {len(files)} files in s3://{bucket}/{folder}/")
    sorted_files = sorted(files, key=lambda m: m["LastModified"])
    file_paths = [f"s3://{bucket}/{f['Key']}"for f in sorted_files]

    log.info(f"Oldest file: {file_paths[0]}")
    log.info(f"Latest file: {file_paths[-1]}")

    return file_paths
