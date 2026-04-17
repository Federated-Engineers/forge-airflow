from airflow.sdk import dag, task
from pendulum import datetime
from airflow.sdk.definitions.context import get_current_context
from business_logic.bieler_zeitwerk.pipeline import run_pipeline


@dag(
    dag_id="bieler_zeitwerk_asset_repair_data",
    start_date=datetime(2026, 4, 10),
    catchup=False,
    schedule="@daily",
    tags=["forge"],
)
def process_asset_repair_data():

    @task()
    def _process_asset_repair_data():
        context = get_current_context()
        return run_pipeline(context)

    _process_asset_repair_data()


process_asset_repair_data()
