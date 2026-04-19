import json
from typing import Any

import awswrangler as wr
import boto3
import gspread
import pandas as pd
from airflow.sdk import Variable


def _get_ssm_paramater(parameter_name: str):
    """
    Retrieve a parameter from AWS Systems Manager (SSM) Parameter Store.

    Args:
        parameter_name (str): The name of the SSM parameter to retrieve.
    Returns:
        dict: The response from SSM containing the parameter
                value and metadata.
    """
    session = boto3.Session()
    ssm = session.client("ssm")
    return ssm.get_parameter(Name=parameter_name)


def _validate_variables() -> dict[str, Any]:
    """
    Retrieve and Validate the required Airflow Variables for \
        the Glaciair data pipeline.

    Returns:
        dict[str, Any]: A dictionary containing the validated variables.
    """
    glaciair_variables = Variable.get("GLACI_AIR", deserialize_json=True)

    ssm_parameter_name: str = glaciair_variables.get("ssm_parameter_name", "")
    s3_path: str = glaciair_variables.get("s3_path", "")  # bucket_name/prefix

    # This expects a JSON list object in the Airflow Variable.
    spreadsheet_names: list[str] = glaciair_variables.get(
        "spreadsheet_names",
        []
    )
    if not isinstance(spreadsheet_names, list):
        raise ValueError("Spreadsheet names must be a JSON List.")
    else:
        for sheet_name in spreadsheet_names:
            if not isinstance(sheet_name, str):
                raise ValueError("Sheet names must be a string.")
    return {
        "ssm_paramater_name": ssm_parameter_name,
        "spreadsheet_names": spreadsheet_names,
        "s3_path": s3_path
    }


def load_gsheets_s3_csv(report_date):
    """
    A function to load google sheets source data into S3 bucket
    """

    # validate airflow variables
    variables = _validate_variables()

    google_service_creds = _get_ssm_paramater(variables["ssm_paramater_name"])
    cred_dict = json.loads(google_service_creds["Parameter"]["Value"])
    s3_path = variables["s3_path"]

    # authenticate google service account
    gc = gspread.service_account_from_dict(cred_dict)

    # open google sheets by name
    for gsheet_name in variables["spreadsheet_names"]:
        spreadsheet = gc.open(gsheet_name)
        # selecting worksheet by its title sheet1
        worksheet = spreadsheet.worksheet("Sheet1")

        # convert google sheet data to pandas dataframe
        sheet_df = pd.DataFrame(worksheet.get_all_records())

        s3_prefix = gsheet_name.lower().replace(' ', '_')
        wr.s3.to_csv(
            df=sheet_df,
            path=f's3://{s3_path}/glaciair/{report_date}/{s3_prefix}.csv',
            index=False
        )

        print(f"Data {gsheet_name} written to s3 bucket successfully!!")
