from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from business_logic.deburf.tasks import run_migration, transform_data

default_args = {
    "owner": "federated_engineers",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="deburf_dag",
    default_args=default_args,
    description="deburf migrate data from RDS to S3 daily pipeline",
    start_date=datetime(2026, 8, 1),
    schedule="@daily",
    catchup=False,
    tags=["deburf"],
) as dag:

    migration_task = PythonOperator(
        task_id="migrate_data_from_RDS_and_load_raw_s3",
        python_callable=run_migration,
    )

    transform_and_load_partition = PythonOperator(
        task_id="transform_raw_to_processed_s3",
        python_callable=transform_data,
    )

    migration_task >> transform_and_load_partition
