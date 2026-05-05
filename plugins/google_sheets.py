import logging
from typing import Dict, List

import gspread
from aws import retrieve_ssm_parameter_value
from google.oauth2.service_account import Credentials

log = logging.getLogger(__name__)


def authenticate_google_sheet(scopes: List) -> gspread.Client:
    """
    Authenticate with Google Sheets API and return an
    authorised gspread client.

    Returns:
        gspread.Client: An authorised gspread client instance
    """
    creds = Credentials.from_service_account_info(
        retrieve_ssm_parameter_value(), scopes=scopes
    )
    client = gspread.authorize(creds)
    return client


def get_google_sheet_records(
    client: gspread.Client, spreadsheet_id: str, worksheet_name: str
) -> List[Dict]:
    """
    Fetch all records from the configured Google Sheet worksheet.
    Args:
        client: Authenticated gspread client.
        spreadsheet_id: id of the Google Sheet worksheet.
        worksheet_name: Name of the Google Sheet worksheet.
    Returns:
        List of dictionaries containing all rows from the worksheet.
    """
    sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    return sheet.get_all_records()


def write_append_df_to_sheet(df, spreadsheet_id, sheetname, google_cred):
    """
    Authenticate with Google Sheets API and
    writes data from a Dataframe to Google Sheet.
    If the Sheet is empty, adds a header to the first row,
    else it appends data from the Dataframe to the Sheets.
    """
    if df.empty:
        log.info("No data to write, skipping...")
        return

    worksheet = google_cred.open_by_key(spreadsheet_id).worksheet(sheetname)

    first_row = worksheet.row_values(1)

    if not first_row:
        log.info("Sheet is empty, writing headers and data...")
        worksheet.append_rows([df.columns.tolist()] + df.values.tolist())
    else:
        log.info("Sheet has data, appending rows only...")
        worksheet.append_rows(df.values.tolist())
