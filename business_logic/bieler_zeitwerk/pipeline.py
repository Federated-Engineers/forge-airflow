from typing import Dict
import io
import boto3
import json
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
from airflow.hooks.base import BaseHook
from airflow.utils.context import Context
from airflow.utils.log.logging_mixin import LoggingMixin

log = LoggingMixin().log

WORKSHEET_NAME = "asset_repair_condition"
BUCKET_NAME = "federated-engineers-staging-forge-datalake"
PREFIX = "asset_repair"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1KdVYhWeu9cWIIXhich_p3p0AOb22nItk1QdP-WWZf8I"
s3_hook = S3Hook(aws_conn_id="aws_airflow_user")


def get_aws_credentials():
    conn = BaseHook.get_connection("aws_airflow_user")
    return conn.login, conn.password, conn.extra_dejson.get("region_name")


access_key, secret_key, region = get_aws_credentials()


def get_google_credentials() -> Dict:
    client = boto3.session.Session().client(
        service_name="ssm",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    response = client.get_parameter(
        Name="/production/google-service-account/credentials"
    )
    return json.loads(response["Parameter"]["Value"])


def get_asset_repair_sheet():
    creds = Credentials.from_service_account_info(
        get_google_credentials(), scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client


def get_all_records(client) -> pd.DataFrame:
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    return df

def copy_to_s3(
    records: pd.DataFrame, dest_bucket: str, dest_key: str
) -> None:
    row_count = len(records)
    log.info(f"Processing {row_count} rows from asset repair worksheet")

    buffer = io.BytesIO()
    csv_data = records.to_csv(index=False)
    buffer.write(csv_data.encode("utf-8"))
    buffer.seek(0)

    s3_hook.load_file_obj(
        file_obj=buffer,
        key=dest_key,
        bucket_name=dest_bucket,
        replace=True
    )

def create_manifest(context: Context, key: str, row_count: int) -> Dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "s3_location": f"s3://{BUCKET_NAME}/{key}",
        "metrics": {
            "row_count": row_count,
        },
        "lineage": {
            "source_type": "google_sheets",
            "source_name": WORKSHEET_NAME,
            "dag_id": context["dag"].dag_id,
            "run_id": context["run_id"],
            "execution_date": context["ds"],
        }
    }


def upload_manifest(manifest: Dict, manifest_key: str) -> None:
    s3_hook.load_string(
        string_data=json.dumps(manifest, indent=2),
        key=manifest_key,
        bucket_name=BUCKET_NAME,
        replace=True
    )



def run_pipeline(context: Context) -> None:
    execution_date = context["ds"]
    google_client = get_asset_repair_sheet()
    data = get_all_records(google_client)

    if data.empty:
        log.error("No records asset repair found")
        raise Exception("No asset repair records found")

    key = f"{PREFIX}/{execution_date}/asset_repair.csv"

    copy_to_s3(
        records = data,
        dest_bucket = BUCKET_NAME,
        dest_key = key
    )
    log.info(f"Successfully copied {len(data)} rows to {BUCKET_NAME}/{key}")


    row_count = len(data)

    manifest_key = f"{PREFIX}/{execution_date}/manifest.json"
    manifest = create_manifest(context, manifest_key, row_count)

    upload_manifest(manifest, manifest_key)

    log.info(f"Manifest uploaded to {manifest_key}")




