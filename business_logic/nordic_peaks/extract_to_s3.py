import logging
from typing import Any

import awswrangler as wr
import boto3
import pandas as pd

logger = logging.getLogger(__name__)
wr.engine.set("python")

GOOGLE_CREDS_SSM_PATH = "/production/google-service-account/credentials"


def write_raw_to_s3(
    records: pd.DataFrame,
    bucket: str,
    key: str,
) -> str:
    """Writes the raw csv to s3 while keeping existing landing object unchanged."""
    s3 = boto3.client("s3")

    try:
        s3.head_object(Bucket=bucket, Key=key)
        return f"s3://{bucket}/{key}"
    except s3.exceptions.ClientError as exc:
        error_code = exc.response.get("Error", {}).get(
            "Code", ""
        )
        if error_code not in {"404", "NoSuchKey", "NotFound"}:
            raise
    uri = f"s3://{bucket}/{key}"
    wr.s3.to_csv(
        df=records,
        path=uri,
        index=False,
        encoding="utf-8"
    )
    return uri


def validate_metadata(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ Validate Google Sheets source metadata. Confirms the input is a non‑empty list of dictionaries and that each dictionary includes all required fields."""

    if not isinstance(metadata, list) or not metadata:
        raise ValueError("GSHEETS_SOURCES must be a non-empty JSON array")

    required_fields = {
        "source_id",
        "spreadsheet_id",
        "worksheet_name",
        "partition_date_column",
    }
    for source in metadata:
        if not isinstance(source, dict):
            raise ValueError(
                "Each GSHEETS_SOURCES entry must be a JSON object"
            )
        missing = required_fields - set(source.keys())
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Source config is missing required fields: {missing_fields}"
            )
    return metadata
