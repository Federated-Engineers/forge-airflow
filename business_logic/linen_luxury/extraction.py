import logging

from airflow.models import Variable

from plugins.database import get_postgres_data
from plugins.google_sheets import (get_google_sheet_data,
                                   google_service_account_auth)

logger = logging.getLogger(__name__)


def write_postgres_dataframe():
    """
    Extracts data from Postgres database using internal modules.
    """
    query = "SELECT * FROM historical.liffey_luxury_order_transactions"

    logger.info("Starting Postgress Extraction from supabase")
    postgres_data = get_postgres_data(conn_id="supabase_postgres", query=query)
    logger.info(f"Successfully extracted {len(postgres_data)} rows from db")

    return postgres_data


def google_sheet_extraction():
    """
    Airflow-specific extraction logic.
    """

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    client = google_service_account_auth(scopes)

    sheet_config = Variable.get("LINEN_LUXURY_SHEET_CONFIG",
                                deserialize_json=True)

    return get_google_sheet_data(
        client=client,
        sheet_id=sheet_config.get("sheet_id").strip(),
        tab_name=sheet_config.get("tab_name").strip(),
    )
