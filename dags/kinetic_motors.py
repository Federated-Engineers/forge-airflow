from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.providers.standard.operators.python import PythonOperator
from business_logic.kinetic_motors.extract_load import extract_load_portugal
from business_logic.kinetic_motors.config import config

spreadsheet_id = config["spreadsheet_id"]
sheetname = config["sheetname"]

default_args = {
    "owner": "Federated-Engineers",
    'depends_on_past': False,
    "start_date": datetime(2026, 4, 18),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="kinetic_motors_daily",
    default_args=default_args,
    schedule="30 7 * * *",
    description="Extract Portugal data from S3 and load to Google Sheets",
    catchup=False,
    tags=["kinetic-mnotors", "S3", "Google_sheets"]
) as dag:

    extract_load_portugal = PythonOperator(
        task_id="extract_load_to_sheet",
        python_callable=extract_load_portugal,
        op_kwargs={
            "spreadsheet_id": spreadsheet_id,
            "sheetname": sheetname,
        },
    )
