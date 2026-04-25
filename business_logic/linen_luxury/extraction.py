import gspread
import pandas as pd
from airflow.models import Connection, Variable
from airflow.providers.google.suite.hooks.sheets import GSheetsHook
from airflow.providers.postgres.hooks.postgres import PostgresHook


def extraction():
    pg_hook = PostgresHook(postgres_conn_id="supabase_postgres")

    pg_data = pg_hook.get_pandas_df(sql="SELECT * FROM historical.liffey_luxury_order_transactions")


    ##google pull
    conn = Connection.get_connection_from_secrets("google_sheets_con")
    

    parms = conn.extra_dejson
    

    if parms and "keyfile_dict" in parms:
        creds = parms.get("keyfile_dict")
    else:
        creds = parms


    if not creds:
        raise ValueError("Could not find credentials in 'google_sheets_con' Extra field!")

    auth = gspread.service_account_from_dict(creds)


    sheet_id = Variable.get("SHEET_NAME").strip()
    tab_name = Variable.get("WORKSHEET_NAME").strip()

    spreadsheet = auth.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(tab_name)

    get_data = worksheet.get_all_values()

    google_data = pd.DataFrame(get_data[1:], columns=get_data[0]) if get_data else pd.DataFrame()
    postgres_data = pd.DataFrame(pg_data)
    
    return google_data, postgres_data