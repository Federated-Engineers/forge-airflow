import gspread
from google.oauth2.service_account import Credentials
from get_parameter import param


def get_google_credentials():
    """google service account credentials"""

    creds_dict = param("/production/google-service-account/credentials")
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]

    credentials = Credentials.from_service_account_info(
        creds_dict, scopes=scopes)
    return gspread.authorize(credentials)
