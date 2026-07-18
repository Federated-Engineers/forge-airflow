import json
from typing import Any

import boto3
import awswrangler as wr
import pandas as pd


def build_landing_key(source: str, run_dt: Any) -> str:
    """Create immutable landing key with day partition and run timestamp suffix."""
    year = run_dt.strftime("%Y")
    month = run_dt.strftime("%m")
    day = run_dt.strftime("%d")
    hhmm = run_dt.strftime("%H%M")
    return (
        f"landing/source={source}/year={year}/month={month}/day={day}/"
        f"{source}_{hhmm}Z.json"
    )


def build_processed_key(source: str, run_dt: Any) -> str:
    """Create deterministic monthly processed key for idempotent retries."""
    year = run_dt.strftime("%Y")
    month = run_dt.strftime("%m")
    return f"processed/source={source}/year={year}/month={month}/{source}.parquet"


def write_snapshot_to_s3_if_missing(
    records: list[dict[str, Any]],
    bucket: str,
    key: str,
) -> str:
    """Write a JSON snapshot once; keep an existing landing object unchanged."""
    s3 = boto3.client("s3")

    try:
        s3.head_object(Bucket=bucket, Key=key)
        return f"s3://{bucket}/{key}"
    except s3.exceptions.ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code not in {"404", "NoSuchKey", "NotFound"}:
            raise

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(records, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{bucket}/{key}"


def read_snapshot_from_s3(s3_uri: str) -> list[dict[str, Any]]:
    """Load a landing snapshot JSON from S3."""
    records = wr.s3.read_json(path=s3_uri)
    if isinstance(records, pd.DataFrame):
        return records.to_dict(orient="records")
    return records


def write_processed_parquet(
    dataframe: pd.DataFrame,
    bucket: str,
    key: str,
    athena_types: dict[str, str],
) -> str:
    """Write a deterministic monthly Parquet object to the processed zone."""
    path = f"s3://{bucket}/{key}"
    wr.s3.to_parquet(
        df=dataframe,
        path=path,
        dataset=False,
        index=False,
        dtype=athena_types or None,
    )
    return path
