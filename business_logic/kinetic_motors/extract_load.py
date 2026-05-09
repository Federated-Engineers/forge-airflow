import logging
from datetime import datetime

import awswrangler as wr
import pandas as pd
from airflow.sdk import Variable

from plugins.google_sheets import (authenticate_google_sheet,
                                   write_append_df_to_sheet)
from plugins.s3_plug import get_lastest_s3_object

log = logging.getLogger(__name__)

CHECKPOINT_KEY = "km_last_processed_date"


def extract_date_from_path(s3_path: str) -> str:
    """
    Extract date from file name
    Example:
    s3://.../km_ops_20260408.parquet -> 20260408
    """
    return s3_path.split("_")[-1].replace(".parquet", "")


def extract_load_portugal(spreadsheet_id, sheetname):
    """
    Extracts Portugal data from S3 parquet files and loads it
    into a Google Sheet.
    The pipeline:
    - Reads files from an S3 bucket/folder
    - Filters data for Portugal records only
    - Duplicate removal based on transaction_id and date
    - Processes only new data based on the last processed date
    - Supports backfill using a specified Airflow Variable (`backfill_date`)

    Behavior:
    - If `backfill_date` is set, it processes all files from that date onward
    - Otherwise it processes only files newer than the last processed date
    - Updates the last processed date after successful execution

    Args:
        spreadsheet_id : Google Sheet ID
        sheetname : Target worksheet name within the Google Sheet
    """
    config = Variable.get("km_config", deserialize_json=True)

    bucket = config["bucket"]
    folder = config["folder"]
    scopes = config["scopes"]
    spreadsheet_id = config["spreadsheet_id"]
    sheetname = config["sheetname"]

    google_cred = authenticate_google_sheet(scopes)

    worksheet = google_cred.open_by_key(spreadsheet_id).worksheet(sheetname)
    existing_data = worksheet.get_all_values()

    if existing_data:
        existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])

        if (
            "transaction_id" in existing_df.columns
            and "date" in existing_df.columns
        ):
            existing_df["transaction_id"] = existing_df[
                "transaction_id"
            ].astype(str)
            existing_df["date"] = existing_df["date"].astype(str)

            existing_keys = (
                existing_df["transaction_id"].str.strip()
                + "_" + existing_df["date"].str.strip()
                )

            existing_keys = set(existing_keys)
        else:
            log.warning(
                "transaction_id or date not found in sheet, skipping dedup"
                )
            existing_keys = set()
    else:
        existing_keys = set()

    last_processed_date = Variable.get(CHECKPOINT_KEY, default=None)
    backfill_date = Variable.get("backfill_date", default=None)

    log.info(f"Last processed date: {last_processed_date}")
    log.info(f"Backfill date: {backfill_date}")

    files = get_lastest_s3_object(bucket, folder)

    files_to_process = []

    for f in files:
        file_date = extract_date_from_path(f)

        file_dt = datetime.strptime(file_date, "%Y%m%d")

        if backfill_date:
            backfill_dt = datetime.strptime(backfill_date, "%Y%m%d")

            if file_dt >= backfill_dt:
                files_to_process.append((f, file_dt))

        else:
            if last_processed_date:
                last_dt = datetime.strptime(last_processed_date, "%Y%m%d")

                if file_dt > last_dt:
                    files_to_process.append((f, file_dt))
            else:
                files_to_process.append((f, file_dt))

    if not files_to_process:
        log.info("No new data to process. Pipeline is up to date.")
        return

    log.info(f"Detected {len(files_to_process)} file(s) to process")

    processed_dates = []

    for s3_path, file_dt in files_to_process:

        log.info(f"Processing: {s3_path}")

        df = wr.s3.read_parquet(s3_path)

        df = df[
            df["plant_country"].str.strip().str.upper() == "PORTUGAL"]
        if df.empty:
            log.warning(f"No Portugal data found in {s3_path}")
            raise ValueError(f"No Portugal data found in {s3_path}")

        df["transaction_id"] = df["transaction_id"].astype(str)
        df["date"] = df["date"].astype(str)
        unique_keys = (
            df["transaction_id"].str.strip() + "_" + df["date"].str.strip())
        dupes = df[unique_keys.isin(existing_keys)]

        if not dupes.empty:
            log.info(f"Found {len(dupes)} duplicate rows in {s3_path}")
            log.info("\n" + dupes.head(2).to_string())

        if existing_keys:
            before = len(df)

            df = df[~unique_keys.isin(existing_keys)]

            after = len(df)

            log.info(f"Deduplicated {before} to {after} rows")

        if df.empty:
            log.info("No new rows after deduplication, skipping write")
            continue

        log.info(f"Writing {len(df)} rows to sheet")

        write_append_df_to_sheet(df, spreadsheet_id, sheetname, google_cred)

        existing_keys.update(unique_keys)

        processed_dates.append(file_dt)

    if processed_dates and not backfill_date:
        latest_date = max(processed_dates).strftime("%Y%m%d")

        Variable.set(CHECKPOINT_KEY, latest_date)
        log.info(f"Checkpoint updated to {latest_date}")

    if backfill_date:
        Variable.delete("backfill_date")
        log.info("Backfill completed and variable cleared")

    log.info("Portugal ETL completed successfully")
