from typing import Any

import pandas as pd
from plugins.AWS.aws_wrangler.S3.wrangler_write import write_csv_data

from business_logic.nordic_peaks.s3_keys import build_landing_folders


def write_raw_to_s3(
    records: pd.DataFrame,
    bucket: str,
    run_datetime: Any,
    gsheet_source: str,
) -> str:
    """Write the raw CSV to S3."""
    landing_key = build_landing_folders(source=gsheet_source,
                                        run_dt=run_datetime)
    landing_zone_path = f"s3://{bucket}/{landing_key}"
    write_csv_data(df=records, bucket=bucket, prefix=landing_key)
    return landing_zone_path


def validate_metadata(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate Google Sheets source metadata.

    Confirms the input is a non-empty list of dictionaries and that
    each dictionary includes all required fields.
    """

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
