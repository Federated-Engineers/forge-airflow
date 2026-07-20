import json
import logging

import gspread
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
