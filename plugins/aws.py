import json
from typing import Dict, List

import boto3
import gspread
from google.oauth2.service_account import Credentials


def retrieve_google_credentials() -> Dict:
    """
    Retrieve Google service account credentials from
    AWS Systems Manager Parameter Store.

    Returns:
        Dict: A dictionary containing the Google service account credentials
    """

    client = boto3.session.Session().client(service_name="ssm")
    response = client.get_parameter(
        Name="/production/google-service-account/credentials"
    )
    return json.loads(response["Parameter"]["Value"])


def authenticate_google_sheet(scopes: List) -> gspread.Client:
    """
    Authenticate with Google Sheets API and return an
    authorised gspread client.

    Returns:
        gspread.Client: An authorised gspread client instance
    """
    creds = Credentials.from_service_account_info(
        retrieve_google_credentials(), scopes=scopes
    )
    client = gspread.authorize(creds)
    return client
