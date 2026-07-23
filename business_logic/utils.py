import io
import json
import logging

import boto3
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_ssm_parameter(ssm_parameter_name: str, region: str) -> str:
    """
    Fetch the value of a parameter from AWS Systems Manager Parameter Store

    Args:
        ssm_parameter_name (str): The name of the parameter to fetch.
        region: (str): The AWS region where the parameter is stored.

    Returns:
        str: The value of the specified parameter.
    """
    client = boto3.client("ssm", region_name=region)
    response = client.get_parameter(
        Name=ssm_parameter_name,
        WithDecryption=True
    )
    ssm_params_value = response["Parameter"]["Value"]
    logger.info(
        f"Fetched SSM parameter {ssm_parameter_name!r} "
        f"from region {region!r}"
    )
    return ssm_params_value


def get_gspread_client(credentials_dict: dict, scopes: list = GOOGLE_SCOPES):
    """
    Authenticate with Google Sheets using credentials provided as a dictionary.

    Args:
        credentials_dict (dict): A dictionary containing the service account \
            credentials.
        scopes (list): A list of scopes for the Google Sheets API.

    Returns:
        gspread.Client: An authenticated gspread client.
    """
    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=scopes
    )
    logger.info("Google Sheets authentication successful")
    return gspread.authorize(credentials)


def get_gspread_client_via_ssm_parameter(ssm_path: str, ssm_param_region: str):
    """
    Authenticate with Google Sheets using credentials stored in \
    AWS SSM Parameter Store.

    Args:
        ssm_path (str): The path to the SSM parameter containing the \
            service account credentials.
        ssm_param_region (str): The AWS region where the SSM parameter \
            is stored.

    Returns:
        gspread.Client: An authenticated gspread client.
    """
    logger.debug(
        f"Fetching Google service account credentials from SSM parameter: "
        f"{ssm_path} in region: {ssm_param_region}"
    )
    credentials_dict = json.loads(
        get_ssm_parameter(ssm_path, ssm_param_region)
    )
    gc = get_gspread_client(credentials_dict)
    return gc


def get_gspread_data(
    gsheet_client, gsheet_id: str, sheet_name: str | None = None
) -> pd.DataFrame:
    """
    Open a Google Sheet by its ID and return its contents as a raw DataFrame.

    Args:
        gsheet_client (gspread.Client): An authenticated gspread client.
        gsheet_id (str): The ID of the Google Sheet to open.
        sheet_name (str | None): The name of the specific sheet to open. \
            If None, the first sheet will be opened.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the specified \
            Google Sheet.
    """

    logger.info(
        f"Fetching data for Google Sheet ID: {gsheet_id!r} "
        f", Sheet Name: {sheet_name if sheet_name else 'Sheet1'!r}"
    )

    workbook = gsheet_client.open_by_key(gsheet_id)

    if sheet_name:
        worksheet = workbook.worksheet(sheet_name)
    else:
        worksheet = workbook.sheet1
    records = worksheet.get_all_records()

    df = pd.DataFrame(records)
    logger.info(f"Fetched {len(df)} rows from sheet ID '{gsheet_id}'")
    return df


def upload_dataframe_to_s3_as_csv(
    df: pd.DataFrame, s3_bucket: str, s3_key: str, region: str
):
    """
    Upload a DataFrame to an S3 bucket as a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to upload.
        s3_bucket (str): The name of the S3 bucket.
        s3_key (str): The S3 key (path) where the CSV file will be stored.
        region (str): The AWS region where the S3 bucket is located.

    Returns:
        None
    """
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    boto3.client("s3", region_name=region).put_object(
        Bucket=s3_bucket,
        Key=s3_key,
        Body=csv_buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )
    logger.info(f"Uploaded DataFrame to s3://{s3_bucket}/{s3_key}")
