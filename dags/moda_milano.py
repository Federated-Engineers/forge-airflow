from airflow.sdk import dag, task
from pendulum import datetime

from business_logic.moda_milano.extract_tables import (copy_orders,
                                                       copy_products)
from business_logic.moda_milano.fulfillments import process_fulfillment_data


@dag(
    dag_id="moda-milano-lakehouse-pipeline",
    start_date=datetime(2026, 5, 5),
    catchup=False,
    schedule="0 0 * * *",
    tags=["forge", "S3", "lakehouse", "Moda Milano"],
)
def process():

    @task()
    def ingest_fulfillment_data():
        return process_fulfillment_data()

    @task()
    def extract_orders_data():
        return copy_orders()

    @task()
    def extract_products_data():
        return copy_products()

    ingest_fulfillment_data()
    extract_orders_data()
    extract_products_data()


process()
