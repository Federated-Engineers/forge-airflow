from typing import Any
import pandas as pd
from plugins.gspread_auth import get_google_sheets_data
import psycopg2


def extract_googlesheets_data(
    pipeline_metadata: dict[str, Any]
) -> pd.DataFrame:
    google_metadata = pipeline_metadata.get("google_sheets_metadata")
    google_credentials_ssm_path = google_metadata["google_credentials_ssm_path"]
    google_sheet_id = google_metadata["google_sheet_id"]
    sheet_name = google_metadata["sheet_name"]

    df = get_google_sheets_data(
        gsheet_id=google_sheet_id,
        ssm_path=google_credentials_ssm_path,
        sheet_name=sheet_name,
    )
    print('Data successfully extracted from google sheets')
    print(df)
    return df


def extract_supasbase_data(pipeline_metadata: dict[str, Any]) -> pd.DataFrame:
    supabase_metadata = pipeline_metadata.get("supabase_conn_metadata")
    try:
        conn = psycopg2.connect(
            host=supabase_metadata["host"],
            database=supabase_metadata["database"],
            user=supabase_metadata["user"],
            password=supabase_metadata["password"]
        )

        print("Successfully connected to Supabase Postgres DB")

        query = (
            "SELECT COUNT(*) "
            "FROM liffey_luxury.liffey_luxury_order_transactions;"
        )

        # convert the response to a pandas DataFrame
        df = pd.read_sql_query(query, conn)
        print('Data successfully extracted from Supabase Postgres DB')
        print(df)
        return df

    except (Exception, psycopg2.Error) as err:
        print(f"An Error occured while connecting to the database: {err}")
        raise
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print('Connection to Postgres DB is closed')
