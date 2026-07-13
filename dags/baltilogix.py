from airflow.sdk import dag, task
from pendulum import datetime

from business_logic.baltilogix_solutions import run_compaction, validate_output


@dag(
    dag_id="baltilogix_compaction_pipeline",
    start_date=datetime(2026, 7, 10),
    catchup=False,
    schedule="0 1 * * *",
    tags=["forge", "S3", "baltilogix", "kafka"],
)
def compact_vehicle_data():

    @task(multiple_outputs=True)
    def compact_and_count_data():
        return run_compaction()

    @task()
    def validate_written_data(source_count: int, output_paths: list):
        validate_output(source_count, output_paths)

    compaction = compact_and_count_data()
    validate_written_data(
        compaction["source_count"],
        compaction["output_paths"]
    )


compact_vehicle_data()
