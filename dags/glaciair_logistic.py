from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from pendulum import datetime

from business_logic.glaciair_logistic.consolidate_glaciair_data import \
    load_gsheet_to_s3

with DAG(
    dag_id='glaciair-logistics-data-sync',
    start_date=datetime(2026, 4, 1),
    catchup=False,
    schedule="0 5 * * *",  # Everyday at 05:00
    tags=["forge", "data-sync", "glaciair", "google-sheets"]
):
    run_pipeline = PythonOperator(
        task_id="load_glaciair_sheets_s3",
        python_callable=load_gsheet_to_s3
    )

    run_pipeline
