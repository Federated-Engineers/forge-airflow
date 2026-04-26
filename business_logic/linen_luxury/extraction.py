import pandas as pd
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook

from plugins.google_sheets import (authenticate_google_sheet,
                                   get_google_sheet_records)


def postgress_extraction():
    """
    Extracts data from Postgres database using internal modules.
    """
    # 1. Postgres Extraction
    pg_hook = PostgresHook(postgres_conn_id="supabase_postgres")
    pg_data = pg_hook.get_pandas_df(
        sql="SELECT * FROM historical.liffey_luxury_order_transactions"
    )

    postgres_data = pd.DataFrame(pg_data)

    return postgres_data


def google_extraction():
    """
    Extracts data from Google Sheets.
    """
    # scopes for Google Sheets
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # Use the existing module to authenticate
    client = authenticate_google_sheet(scopes)
    sheet_config = Variable.get(
        "LINEN_LUXURY_SHEET_CONFIG",
        deserialize_json=True
    )

    # Get IDs from Airflow Variables
    sheet_id = sheet_config.get("sheet_id").strip()
    tab_name = sheet_config.get("tab_name").strip()

    # Use the existing module to fetch data
    # This returns a List of Dictionaries
    records = get_google_sheet_records(client, sheet_id, tab_name)

    # Convert to DataFrame
    google_data = pd.DataFrame(records)

    return google_data
