import json
import logging
from typing import Any

import boto3
import pandas as pd

from plugins.gspread_auth import authenticate_airflow

logger = logging.getLogger(__name__)

GOOGLE_CREDS_SSM_PATH = "/production/google-service-account/credentials"


def get_google_sheets_data(
    gsheet_id: str,
    ssm_path: str = GOOGLE_CREDS_SSM_PATH,
    sheet_name: str | None = None,
) -> pd.DataFrame:
    """
    Open a Google Sheet by its ID and return its contents as a raw DataFrame.
    """
    if not gsheet_id:
        raise ValueError("gsheet_id is required")

    # Authenticate with Google Sheets using credentials stored in AWS SSM
    auth_output = authenticate_airflow(ssm_path)
    workbook = auth_output.open_by_key(gsheet_id)

    if sheet_name:
        worksheet = workbook.worksheet(sheet_name)
    else:
        worksheet = workbook.sheet1
    records = worksheet.get_all_records()

    df = pd.DataFrame(records)
    logger.info("Fetched %d rows from sheet ID '%s'", len(df), gsheet_id)
    return df


def write_raw_json_to_s3(
    records: list[dict[str, Any]],
    bucket: str,
    key: str,
) -> str:
    """Write a JSON snapshot once; keep existing landing object unchanged."""
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

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(records, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{bucket}/{key}"


def validate_metadata(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
