import json
from typing import Any

import boto3
import awswrangler as wr
import pandas as pd


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
