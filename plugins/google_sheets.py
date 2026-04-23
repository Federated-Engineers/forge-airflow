from typing import List

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
