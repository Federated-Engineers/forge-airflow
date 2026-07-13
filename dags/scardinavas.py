from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from business_logic.scardinavas.pipeline import run_load, run_processed_load

default_args = {
    "owner": "anthony",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="spreadsheets_to_s3_partitioned_pipeline",
    default_args=default_args,
    description="Extract Google Sheets to raw S3, then transform to processed partitioned S3",
    start_date=datetime(2026, 7, 9),
    schedule=None,
    catchup=False,
    tags=["google-sheets", "s3", "awswrangler"],
) as dag:

    extract_and_load_raw_task = PythonOperator(
        task_id="extract_google_sheets_and_load_raw_s3",
        python_callable=run_load,
    )

    transform_and_load_partition_task = PythonOperator(
        task_id="transform_raw_to_processed_s3",
        python_callable=run_processed_load,
    )

    extract_and_load_raw_task >> transform_and_load_partition_task
    