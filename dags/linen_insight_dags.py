from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from pendulum import datetime

from business_logic.linen_luxury.extraction import (google_extraction,
                                                    postgress_extraction)
from business_logic.linen_luxury.load import move_file_s3


def run_all_scripts():
    """
    Executes the extraction and loading scripts for Liffey Linens.
    """
    postgres_data = postgress_extraction()
    google_data = google_extraction()

    move_file_s3(
        google_data,
        "lll/influencers_data/influencer_data.parquet",
        "influencer_transactions"
    )

    move_file_s3(
        postgres_data,
        "lll/orders_data/orders_data.parquet",
        "order_transactions"
    )


with DAG(
    dag_id="Liffey_Linens_Insights",
    start_date=datetime(2026, 4, 22),
    schedule="0 */1 * * *",
    catchup=False
) as dag:

    run_etl_script_to_s3 = PythonOperator(
        task_id="run_all_scripts",
        python_callable=run_all_scripts,
    )

    run_etl_script_to_s3
