import json
import logging

import awswrangler as wr
import boto3
from airflow.sdk import Variable

from plugins.google_auth import get_google_credentials

log = logging.getLogger(__name__)

config = json.loads(Variable.get("km_config"))
bucket = config["bucket"]
folder = config["folder"]
VARIABLE_KEY = "km_loaded_files"


def extract_portugal(file_key):
    log.info(f"Reading {file_key} from S3")

    df = wr.s3.read_parquet(f"s3://{bucket}/{file_key}")
    filtered_df = df[df["plant_country"].str.strip().str.upper() == 'PORTUGAL']
    if filtered_df.empty:
        log.warning("No Portugal records found.")

    return filtered_df


def write_df_to_sheet(df, spreadsheet_id, sheetname):
    """Appends data to google sheets"""
    google_cred = get_google_credentials()
    worksheet = google_cred.open_by_key(spreadsheet_id).worksheet(sheetname)
    first_row = worksheet.row_values(1)
    if not first_row:
        log.info("Sheet is empty, writing headers and data...")
        worksheet.append_rows([df.columns.tolist()] + df.values.tolist())
    else:
        log.info("Sheet has data, appending rows only...")
        worksheet.append_rows(df.values.tolist())


def extract_load_portugal(spreadsheet_id, sheetname):
    """Extracts Portugal data from s3 and loads to google sheet"""
    s3 = boto3.client("s3")
    all_files = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=f"{folder}/"
       ).get("Contents", [])
    loaded_files = json.loads(Variable.get(VARIABLE_KEY, default="[]"))

    for file in all_files:
        file_key = file["Key"]

        if file_key in loaded_files:
            log.info(f"{file_key} already loaded, skipping.")
            continue

        df = extract_portugal(file_key)
        write_df_to_sheet(df, spreadsheet_id, sheetname)
        loaded_files.append(file_key)
        Variable.set(VARIABLE_KEY, json.dumps(loaded_files))
        log.info(f'Successfully loaded {file_key}, {len(df)} rows updated')
