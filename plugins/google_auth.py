import json

import gspread
from get_parameter import param
from google.oauth2.service_account import Credentials


def get_google_credentials():
    """google service account credentials"""

    creds_str = param("/production/google-service-account/credentials")
    creds_dict = json.loads(creds_str)
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]

    credentials = Credentials.from_service_account_info(
        creds_dict, scopes=scopes)
    return gspread.authorize(credentials)
