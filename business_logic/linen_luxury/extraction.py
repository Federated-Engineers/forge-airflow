import logging

import pandas as pd
from airflow.models import Variable

from plugins.database import get_postgres_data
from plugins.google_sheets import (authenticate_google_sheet,
                                   get_google_sheet_records)

logger = logging.getLogger(__name__)


def postgress_extraction():
    """
    Extracts data from Postgres database using internal modules.
    """
    query = "SELECT * FROM historical.liffey_luxury_order_transactions"

    logger.info("Starting Postgress Extraction from supabase")
    postgres_data = get_postgres_data(conn_id="supabase_postgres", query=query)
    logger.info(
        f"Successfully extracted {len(postgres_data)} rows from supabase"
    )

    return postgres_data


def google_sheet_extraction():
    """
    Extracts data from Google Sheet.
    """

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    logger.info("Starting google sheets extraction....")

    client = authenticate_google_sheet(scopes)
    sheet_config = Variable.get("LINEN_LUXURY_SHEET_CONFIG",
                                deserialize_json=True)

    sheet_id = sheet_config.get("sheet_id").strip()
    tab_name = sheet_config.get("tab_name").strip()

    records = get_google_sheet_records(client, sheet_id, tab_name)

    google_data = pd.DataFrame(records)
    logger.info(
        f"Sucessfully extracted {len(google_data)} rows of data."
    )

    return google_data
