import json
import logging

import boto3
from airflow.sdk import Variable

from plugins.extract_load_portugal import extract_portugal, write_df_to_sheet
from plugins.google_sheets import authenticate_google_sheet

log = logging.getLogger(__name__)


def extract_load_portugal(spreadsheet_id, sheetname):
    """Extracts Portugal data from s3 and loads to google sheet.

    Args:
        spreadsheet_id: The spreadsheet id for the Google sheet
        sheetname: The sheetname where data will be written
    """
    config = json.loads(Variable.get("km_config"))
    bucket = config["bucket"]
    folder = config["folder"]
    scopes = config["scopes"]
    VARIABLE_KEY = config["loaded_files_key"]

    google_cred = authenticate_google_sheet(scopes)
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

        df = extract_portugal(file_key, bucket)
        write_df_to_sheet(df, spreadsheet_id, sheetname, google_cred)

        loaded_files.append(file_key)
        Variable.set(VARIABLE_KEY, json.dumps(loaded_files))

        log.info(f"Successfully loaded {file_key}, {len(df)} rows updated")
