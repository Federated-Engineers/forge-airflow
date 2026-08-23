import datetime
from typing import Any

from airflow.sdk import Variable, dag, get_current_context, task

from business_logic.liffey_luxury_linens.extract import (
    extract_googlesheets_data, extract_supasbase_data)

DAG_ID = "Liffey_Luxury_Linens_Pipeline"


@dag(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2026, 8, 14),
    schedule="0 1 * * *",
    catchup=False,
    tags=["google-sheets", "postgres", "supabase", "liffy-lux-linens"],
    max_active_runs=1
)
def liffey_pipeline():
    @task(task_id="initiate_pipeline")
    def initiate_pipline() -> dict[str, Any]:
        context = get_current_context()
        run_datetime = context["logical_date"].in_timezone("UTC")
        bucket_name = Variable.get("LIFFEY_BUCKET_NAME")
        google_sheets_metadata = Variable.get(
            "GOOGLE_SHEETS_METADATA", deserialize_json=True)
        supabase_conn_metadata = Variable.get(
            "SUPABASE_CONN_METADATA", deserialize_json=True)

        return {
            "run_datetime": run_datetime,
            "bucket_name": bucket_name,
            "google_sheets_metadata": google_sheets_metadata,
            "supabase_conn_metadata": supabase_conn_metadata,
        }

    @task(task_id="extract_google_sheets")
    def extract_google_sheets(pipeline_metadata: dict[str, Any]) -> Any:
        df = extract_googlesheets_data(pipeline_metadata)
        return df

    @task(task_id="extract_supabase_data")
    def extract_supabase_data(pipeline_metadata: dict[str, Any]) -> Any:
        df = extract_supasbase_data(pipeline_metadata)
        return df

    @task(task_id="load_raw_data")
    def load_raw_data(pipeline_metadata, gsheets_data, supabase_data) -> Any:
        from business_logic.liffey_luxury_linens.load import load_raw_to_s3
        loaded_data = load_raw_to_s3(
            pipeline_metadata, gsheets_data, supabase_data)
        return loaded_data

    @task(task_id="write_to_curated_zone")
    def write_to_curated_zone_task(pipeline_metadata, loaded_data) -> None:
        from business_logic.liffey_luxury_linens.curate_data import \
            write_to_curated_zone

        bucket_name = pipeline_metadata["bucket_name"]
        run_datetime = pipeline_metadata["run_datetime"]
        write_to_curated_zone(loaded_data, bucket_name, run_datetime)

    pipeline_metadata = initiate_pipline()
    gsheets_data = extract_google_sheets(pipeline_metadata)
    supabase_data = extract_supabase_data(pipeline_metadata)
    loaded_data = load_raw_data(pipeline_metadata, gsheets_data, supabase_data)
    write_to_curated_zone_task(pipeline_metadata, loaded_data)


dag = liffey_pipeline()
