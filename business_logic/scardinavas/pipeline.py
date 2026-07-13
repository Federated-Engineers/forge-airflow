import logging
from datetime import datetime

import awswrangler as wr
import pandas as pd

from business_logic.scardinavas.config import (date_columns, gsheet_ids,
                                               bucket_name, glue_database)
from plugins.gspread_auth import get_data

logger = logging.getLogger(__name__)
wr.engine.set("python")


def gdrive_extract():
    dataframes = {}
    for source_name, gsheet_id in gsheet_ids.items():
        df = get_data(gsheet_id)
        dataframes[source_name] = df
        logger.info("Loaded %d rows for '%s'", len(df), source_name)

    return dataframes


data = gdrive_extract()


def load_to_s3(dataframes, logical_date):
    """
    Load each extracted DataFrame into its own S3 raw folder,
    partitioned by the DAG's logical date (not wall-clock time).
    """
    extraction_date = logical_date.strftime("%Y-%m-%d")

    for source_name, df in dataframes.items():
        s3_path = (
            f"s3://{bucket_name}/raw/{source_name}/"
            f"{source_name}_{extraction_date}.csv"
        )

        wr.s3.to_csv(
            df=df,
            path=s3_path,
            index=False,
            encoding="utf-8",
        )

        logger.info("Loaded %s to %s", source_name, s3_path)


def run_load(logical_date):
    """
    Run the full extract and load process.
    """
    dataframes = gdrive_extract()
    load_to_s3(dataframes, logical_date)

    logger.info("All data loaded successfully to S3.")


def create_glue_database():
    wr.catalog.create_database(name=glue_database, exist_ok=True)
    logger.info("Glue database ready: %s", glue_database)


def process_to_partitioned_s3(dataset_name, logical_date):
    extraction_date = logical_date.strftime("%Y-%m-%d")

    raw_path = (
        f"s3://{bucket_name}/raw/{dataset_name}/"
        f"{dataset_name}_{extraction_date}.csv"
    )
    processed_path = f"s3://{bucket_name}/processed/{dataset_name}/"

    df = wr.s3.read_csv(path=raw_path, encoding="utf-8")

    date_col = date_columns[dataset_name]
    df[date_col] = pd.to_datetime(df[date_col])

    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.month
    df["day"] = df[date_col].dt.day

    wr.s3.to_parquet(
        df=df,
        path=processed_path,
        dataset=True,
        mode="overwrite_partitions",
        partition_cols=["year", "month", "day"],
        database=glue_database,
        table=dataset_name,
    )

    logger.info("%s processed successfully", dataset_name)


def run_processed_load(logical_date):
    create_glue_database()

    for dataset_name in ["orders", "shipments", "payments"]:
        process_to_partitioned_s3(dataset_name, logical_date)


run_load(logical_date=datetime.now())

if __name__ == "__main__":
    run_processed_load(logical_date=datetime(2026, 7, 1))
