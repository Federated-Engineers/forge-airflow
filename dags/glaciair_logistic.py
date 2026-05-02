from datetime import datetime, timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from business_logic.glaciair_logistic.consolidate_glaciair_data import \
    load_gsheet_to_s3

default_args = {
    "owner": "Federated-Engineers",
    "retries": 2,
    "retry_delay": timedelta(seconds=10)
}

with DAG(
    dag_id='glaciair-logistics-data-sync',
    default_args=default_args,
    start_date=datetime(2026, 4, 1),
    catchup=False,
    schedule="0 5 * * *",  # Everyday at 05:00
    tags=["forge", "data-sync", "glaciair", "google-sheets"]
):
    load_glaciair_sheets_s3 = PythonOperator(
        task_id="load_glaciair_sheets_s3",
        python_callable=load_gsheet_to_s3
    )

    load_glaciair_sheets_s3
