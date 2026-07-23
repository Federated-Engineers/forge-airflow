import json
import logging

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from plugins.aws import get_ssm_parameter

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

GOOGLE_CREDS_SSM_PATH = "/production/google-service-account/credentials"


def authenticate_airflow(
    ssm_path: str = GOOGLE_CREDS_SSM_PATH,
) -> gspread.Client:
    """
    Authenticate with Google Sheets using credentials stored in AWS SSM.
    """
    credentials_dict = json.loads(get_ssm_parameter(ssm_path))

    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=SCOPES,
    )

    logger.info("Google Sheets authentication successful")
    return gspread.authorize(credentials)


def get_google_sheets_data(
    gsheet_id: str,
    ssm_path: str = GOOGLE_CREDS_SSM_PATH,
    sheet_name: str | None = None,
) -> pd.DataFrame:
    """
    Open a Google Sheet by its ID and return its contents as a raw DataFrame.
    """
    if not gsheet_id:
        raise ValueError("gsheet_id is required")

    # Authenticate with Google Sheets using credentials stored in AWS SSM
    auth_output = authenticate_airflow(ssm_path)
    workbook = auth_output.open_by_key(gsheet_id)

    if sheet_name:
        worksheet = workbook.worksheet(sheet_name)
    else:
        worksheet = workbook.sheet1
    records = worksheet.get_all_records()

    df = pd.DataFrame(records)
    logger.info("Fetched %d rows from sheet ID '%s'", len(df), gsheet_id)
    return df
