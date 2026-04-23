from typing import Dict, List

import gspread
from aws import retrieve_ssm_parameter_value
from google.oauth2.service_account import Credentials


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
