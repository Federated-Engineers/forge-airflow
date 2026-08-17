from typing import Any
import pandas as pd
from plugins.gspread_auth import get_google_sheets_data
import psycopg2
from plugins.AWS.aws_wrangler.S3.wrangler_write import write_csv_data


def create_supabase_conn(connection: list[dict[str, Any]]) -> Any:
    pass


def extract_googlesheets_data(
    pipeline_metadata: dict[str, Any]
) -> pd.DataFrame:
    google_metadata = pipeline_metadata.get("google_sheets_metadata")
    print(google_metadata)
    google_credentials_ssm_path = google_metadata["google_credentials_ssm_path"]
    google_sheet_id = google_metadata["google_sheet_id"]
    sheet_name = google_metadata["sheet_name"]
    print("pipeline_metadata")
    df = get_google_sheets_data(
        gsheet_id=google_sheet_id,
        ssm_path=google_credentials_ssm_path,
        sheet_name=sheet_name,
    )
    print('Data successfully extracted from google sheets')
    print(df)
    return df


def extract_supasbase_data(pipeline_metadata: dict[str, Any]):
    try:
        conn = psycopg2.connect(
            host="aws-1-eu-west-1.pooler.supabase.com",
            database="postgres",
            user="postgres.lksygmgwphnbbvdbgzaw",
            password="pd0S4b4DwgE0IH6L63lq"
        )

        print("Successfully connected to Supabase Postgres DB")

        cur = conn.cursor()

        query = (
            "SELECT COUNT(*) "
            "FROM liffey_luxury.liffey_luxury_order_transactions;"
        )
        response = cur.execute(query)
        print(response)

    except (Exception, psycopg2.Error) as err:
        print(f"An Error occured while connecting to the database: {err}")
    finally:
        if 'conn' in locals() and conn:
            cur.close()
            conn.close()
            print('Connection to Postgres DB is closed')
