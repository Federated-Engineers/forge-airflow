from datetime import date

import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from plugins.google_sheets import (authenticate_google_sheet,
                                   get_google_sheet_records)
from plugins.logger import log

config = Variable.get("bieler_zeitwerk_config", deserialize_json=True)
s3_hook = S3Hook()


def get_all_records() -> pd.DataFrame:
    """
    Fetch all records from a Google Sheet worksheet by calling
    `get_google_sheet_records()` and transform them into a pandas DataFrame.

    Returns:
        DataFrame containing all rows from the worksheet.
    """
    spreadsheet_id = config.get("spreadsheet_id")
    worksheet_name = config.get("worksheet_name")
    google_client = authenticate_google_sheet(config["scopes"])

    data = get_google_sheet_records(
        google_client, spreadsheet_id, worksheet_name
    )
    records_df = pd.DataFrame(data)

    return records_df


def copy_to_s3(records: pd.DataFrame, dest_bucket: str, dest_key: str) -> None:
    """
    Upload a DataFrame as a CSV string to S3.

    Args:
        records: DataFrame to upload.
        dest_bucket: Target S3 bucket name.
        dest_key: Target S3 object key (path).
    """
    row_count = len(records)
    log.info(f"Processing {row_count} rows from asset repair worksheet")
    csv_data = records.to_csv(index=False)

    s3_hook.load_string(
        string_data=csv_data, key=dest_key,
        bucket_name=dest_bucket, replace=True
    )


def run_pipeline() -> None:
    """
    Orchestrate the asset repair data pipeline.

    Authenticates with Google Sheets, fetches all records, and uploads
    them as a CSV to S3 in a date partitioned folder.

    Raises an exception if no records are found.
    """
    extraction_date = str(date.today())
    data = get_all_records()

    if data.empty:
        raise Exception("No asset repair records found")

    key = f"{config['prefix']}/{extraction_date}/asset_repair.csv"

    copy_to_s3(records=data, dest_bucket=config["bucket_name"], dest_key=key)
    log.info(
        f"Successfully copied {len(data)} rows to "
        f"{config['bucket_name']}/{key}"
    )
