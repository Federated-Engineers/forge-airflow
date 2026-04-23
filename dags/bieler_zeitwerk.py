from airflow.sdk import dag, task
from pendulum import datetime

from business_logic.bieler_zeitwerk.process_asset_repairs import run_pipeline


@dag(
    dag_id="bieler_zeitwerk_asset_repair_data",
    start_date=datetime(2026, 4, 10),
    catchup=False,
    schedule="0 6 * * *",
    tags=["forge", "google sheets", "SFTP", "bieler zeitwerk"],
)
def process_asset_repair_data():

    @task()
    def process_asset_repair_sheets():
        return run_pipeline()

    process_asset_repair_sheets()


process_asset_repair_data()
