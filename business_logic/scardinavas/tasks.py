import logging

from business_logic.scardinavas.extract import gdrive_extract, load_to_s3
from business_logic.scardinavas.load_partition import process_to_partitioned_s3

# from datetime import datetime


logger = logging.getLogger(__name__)

DATASETS = ["orders", "shipments", "payments"]


def run_load(logical_date):
    """Extract from Google Sheets and load raw CSVs to S3."""
    dataframes = gdrive_extract()
    load_to_s3(dataframes, logical_date)

    logger.info("All data loaded successfully to S3.")


def run_processed_load(logical_date):
    """Transform raw S3 data into partitioned Parquet, registered in Glue."""

    for dataset_name in DATASETS:
        process_to_partitioned_s3(dataset_name, logical_date)
