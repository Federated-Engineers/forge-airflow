import logging

import awswrangler as wr
from plugins.gspread_auth import get_data

from business_logic.scardinavas.config import bucket_name, gsheet_ids

logger = logging.getLogger(__name__)


def gdrive_extract():
    """Extract all configured Google Sheets
    into DataFrames keyed by source name.
    """
    dataframes = {}
    for source_name, gsheet_id in gsheet_ids.items():
        df = get_data(gsheet_id)
        dataframes[source_name] = df
        logger.info("Loaded %d rows for '%s'", len(df), source_name)

    return dataframes


# data = gdrive_extract()


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
