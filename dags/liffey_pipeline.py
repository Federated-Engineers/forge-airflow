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

    # @task(task_id="extract_supabase_data")
    # def extract_supabase_data() -> Any:
    #     df = extract_supasbase_data()
    #     return df

    # @task(task_id="load_raw_data")
    # def load_raw_data(gsheets_data, supabase_data) -> Any:
    #     pass

    pipeline_metadata = initiate_pipline()
    gsheets_data = extract_google_sheets(pipeline_metadata)
    # supabase_data = extract_supabase_data(pipeline_metadata)
    # loaded_data = load_raw_data(gsheets_data, supabase_data)
    print("pipeline_metadata", pipeline_metadata)


dag = liffey_pipeline()
