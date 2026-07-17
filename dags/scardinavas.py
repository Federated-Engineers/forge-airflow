from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from business_logic.scardinavas.tasks import run_load, run_processed_load

default_args = {
    "owner": "federated_engineers",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="scardinavas_dag",
    default_args=default_args,
    description="scardinavas Extract Sheets to S3 daily pipeline",
    start_date=datetime(2026, 7, 9),
    schedule="@daily",
    catchup=False,
    tags=["scardinavas", "google-sheets"],
) as dag:

    extract_and_load_raw = PythonOperator(
        task_id="extract_google_sheets_and_load_raw_s3",
        python_callable=run_load,
    )

    transform_and_load_partition = PythonOperator(
        task_id="transform_raw_to_processed_s3",
        python_callable=run_processed_load,
    )

    extract_and_load_raw >> transform_and_load_partition
