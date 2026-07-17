"""DAG for loading a Google Spreadsheet into S3.

The task reads a worksheet from Google Sheets using a service account JSON,
converts the rows to CSV, and uploads the result to S3.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from airflow.sdk import Variable, dag, task
from airflow.sdk.types import DagRunProtocol

from business_logic.utils import (get_gspread_client_via_ssm_parameter,
                                  get_gspread_data,
                                  upload_dataframe_to_s3_as_csv)

DAG_ID: str = "alpenmechanik_load_to_s3"

default_args = {
    "owner": "Federated-Engineers",
    "depends_on_past": False,
    "start_date": datetime(2026, 7, 15, tzinfo=timezone.utc),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id=DAG_ID,
    schedule=None,
    catchup=False,
    default_args=default_args,
    max_active_runs=1,
    tags=[
        'alpenmechanik', 'sftp', 'transfer', 'asset-repair',
        'google-sheets', 's3'
    ]
)
def alpenmechanik_load_to_s3():
    """
    ### Main DAG function to load AlpenMechanik's `Asset Repair Condition` \
    google spreadsheet to S3 as CSV Files.
    """

    @task()
    def loads_gsheet_to_s3(dag_run: DagRunProtocol):
        """
        Load a Google Sheet into S3 as a CSV file.
        """

        variables: dict = Variable.get(
            "ALPENMECHANIK_S3_LOAD",
            deserialize_json=True
        )

        google_spreadsheet_id = variables.get("GOOGLE_SPREADSHEET_ID")
        s3_bucket_name = variables.get("S3_BUCKET")
        service_account_ssm_param_path = variables.get(
            "GOOGLE_SERVICE_ACCOUNT_SSM_PARAMETER"
        )

        if not google_spreadsheet_id:
            raise ValueError(
                "GOOGLE_SPREADSHEET_ID must be set in Airflow Variables."
            )
        if not s3_bucket_name:
            raise ValueError("S3_BUCKET must be set in Airflow Variables.")
        if not service_account_ssm_param_path:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_SSM_PARAMETER must be set in "
                "Airflow Variables."
            )

        ssm_param_region = (
            variables.get("SSM_PARAM_REGION")
            or
            variables.get("REGION")
        )
        gc = get_gspread_client_via_ssm_parameter(
            service_account_ssm_param_path,
            ssm_param_region=ssm_param_region
        )

        df = get_gspread_data(
            gc,
            google_spreadsheet_id,
            sheet_name=variables.get("WORKSHEET_NAME")
        )

        logical_date = dag_run.logical_date.strftime("%Y-%m-%d")
        s3_key = os.path.join(
            variables.get("S3_PREFIX"),
            f"asset_repair_condition_{logical_date}.csv"
        )

        upload_dataframe_to_s3_as_csv(
            df,
            s3_bucket_name,
            s3_key,
            region=variables.get("S3_BUCKET_REGION") or variables.get("REGION")
        )

    loads_gsheet_to_s3()


alpenmechanik_load_to_s3()
