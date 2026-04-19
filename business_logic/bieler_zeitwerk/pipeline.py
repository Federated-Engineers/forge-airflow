from datetime import date

import gspread
import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.log.logging_mixin import LoggingMixin

from plugins.aws import authenticate_google_sheet

log = LoggingMixin().log
s3_hook = S3Hook(aws_conn_id="aws_airflow_user")

config = Variable.get("bieler_zeitwerk_config")


def get_all_records(client: gspread.Client) -> pd.DataFrame:
    """
    Fetch all records from the configured Google Sheet worksheet.
    Args:
        client: Authenticated gspread client.
    Returns:
        DataFrame containing all rows from the worksheet.
    """
    sheet = client.open_by_key(config["spreadsheet_id"]).worksheet(
        config["worksheet_name"]
    )

    data = sheet.get_all_records()
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
        string_data=csv_data,
        key=dest_key,
        bucket_name=dest_bucket,
        replace=True
    )


def run_pipeline() -> None:
    """
    Orchestrate the asset repair data pipeline.

    Authenticates with Google Sheets, fetches all records, and uploads
    them as a CSV to S3 in a date partitioned folder.

    Raises an exception if no records are found.
    """
    extraction_date = str(date.today())
    google_client = authenticate_google_sheet(config["scopes"])
    data = get_all_records(google_client)

    if data.empty:
        log.error("No records asset repair found")
        raise Exception("No asset repair records found")

    key = f"{config['prefix']}/{extraction_date}/asset_repair.csv"

    copy_to_s3(records=data, dest_bucket=config["bucket_name"], dest_key=key)
    log.info(
        f"Successfully copied {len(data)} rows to "
        f"{config['bucket_name']}/{key}"
    )
