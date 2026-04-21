import logging
import os

import awswrangler as wr
import boto3
import gspread
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_ssm_paramater(parameter_name: str):
    """
    Retrieve a parameter from AWS Systems Manager (SSM) Parameter Store.
    The paramater name cannot contain spaces.

    Args:
        parameter_name (str): The name or Amazon Resource Name (ARN) \
            of the SSM parameter to retrieve.
    Returns:
        dict: The response from SSM containing the parameter
                value and metadata.
    """

    logger.info(f"Retrieving SSM Parameter: {parameter_name!r}")

    session = boto3.Session()
    ssm = session.client("ssm")
    return ssm.get_parameter(Name=parameter_name)


def load_gsheet_to_s3(
    gsheet_name: str,
    s3_bucket: str,
    s3_prefix: str,
    service_credentials: dict,
    format: str = "csv",
    worksheet_name: str = "Sheet1"
):
    """
    Load a Google Sheet worksheet into an S3 object.

    Args:
        gsheet_name (str): Name of the Google Sheet to read.
        s3_bucket (str): Name of the S3 bucket where the file will be uploaded.
        s3_prefix (str): Prefix for the S3 object key.
        service_credentials (dict): SSM parameter response containing the
            service account JSON in `Parameter.Value`.
        worksheet_name (str): Worksheet title to read. Defaults to "Sheet1".

    Returns:
        S3 Object Path: The Object is written to S3.
    """

    # authenticate google service account
    gc = gspread.service_account_from_dict(service_credentials)

    spreadsheet = gc.open(gsheet_name)
    # selecting worksheet by its title sheet1
    worksheet = spreadsheet.worksheet(worksheet_name)

    # convert google sheet data to pandas dataframe
    sheet_df = pd.DataFrame(worksheet.get_all_records())

    s3_path = os.path.join(
        "s3://",
        s3_bucket,
        s3_prefix,
        f"{gsheet_name}.{format}"
    )

    if format == "csv":
        wr.s3.to_csv(
            df=sheet_df,
            path=s3_path,
            index=False
        )
    elif format == "parquet":
        wr.s3.to_parquet(
            df=sheet_df,
            path=s3_path,
            index=False
        )
    elif format == "json":
        wr.s3.to_json(
            df=sheet_df,
            path=s3_path,
            orient="records",
            lines=True
        )
    elif format == "excel":
        wr.s3.to_excel(
            df=sheet_df,
            path=s3_path,
            index=False
        )
    else:
        raise ValueError(
            f"Unsupported format: {format}. "
            "Supported formats are: csv, parquet, json, excel."
        )

    logger.info(
        f"Data {gsheet_name} written to s3 path {s3_path} successfully!!"
    )

    return s3_path
