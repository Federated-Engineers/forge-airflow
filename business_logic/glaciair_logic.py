import json
import os
from typing import Any

import boto3
import gspread
import pandas as pd
import awswrangler as wr
from airflow.sdk import Variable


def _get_ssm_paramater(parameter_name: str):
    '''
    Function to get SSM parameter using boto3
    '''
    session = boto3.Session()
    ssm = session.client("ssm")
    return ssm.get_parameter(Name=parameter_name)


def _validate_variables() -> dict[str, Any]:
    '''
    Function to validate airflow variables
    '''
    ssm_parameter_name: str = Variable.get("GLACIAIR_SSM_PARAMETER")
    s3_path: str = Variable.get("GLACIAIR_S3_PATH") # bucket_name/prefix

    # This expects a JSON list object in the Airflow Variable. For Example ["Sheet1", "Sheet3", "Sheet6"]
    spreadsheet_names_airflow_var_name: str = "GLACIAIR_SPREADSHEETS"
    spreadsheet_names: list[str] = Variable.get(spreadsheet_names_airflow_var_name, deserialize_json=True)
    if not isinstance(spreadsheet_names, list):
        raise ValueError(f"Airflow variable {spreadsheet_names_airflow_var_name} must be a JSON List.")
    else:
        for sheet_name in spreadsheet_names:
            if not isinstance(sheet_name, str):
                raise ValueError(f"Sheet names defined in {spreadsheet_names_airflow_var_name}, must be a string.")
            
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
        
        # selecting worksheet by its title. All the spreadsheets has just one sheet named sheet1
        worksheet = spreadsheet.worksheet("Sheet1")

        # convert google sheet data to pandas dataframe
        sheet_df = pd.DataFrame(worksheet.get_all_records())

        s3_prefix = gsheet_name.lower().replace(' ', '_')
        wr.s3.to_csv(
            df=sheet_df,
            path=f's3://{s3_path}/glaciair_logistic/{report_date}/{s3_prefix}.csv',
            index=False
        )

        print("Data written to s3 bucket successfully!!")
