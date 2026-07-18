import datetime
from typing import Any

from airflow.decorators import dag, get_current_context, task
from airflow.models import Variable

from business_logic.google_sheets.sheets import (
    fetch_worksheet_records,
    parse_service_account_json,
)
from business_logic.google_sheets.storage import (
    build_landing_key,
    build_processed_key,
    read_snapshot_from_s3,
    write_processed_parquet,
    write_snapshot_to_s3_if_missing,
)
from business_logic.google_sheets.transform import records_to_typed_dataframe

DAG_ID = "google-sheets-extract"


@dag(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2024, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["google-sheets", "ingestion"],
    max_active_runs=1,
)
def google_sheets_extract_dag():
    @task(task_id="load_sources")
    def load_sources() -> list[dict[str, Any]]:
        sources = Variable.get("GSHEETS_SOURCES", deserialize_json=True)
        if not isinstance(sources, list) or not sources:
            raise ValueError("GSHEETS_SOURCES must be a non-empty JSON array")

        required_fields = {"source", "spreadsheet_id", "worksheet_name"}
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError(
                    "Each GSHEETS_SOURCES entry must be a JSON object")
            missing = required_fields - set(source.keys())
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise ValueError(
                    f"Source config is missing required fields: {missing_fields}"
                )
        return sources

    @task(task_id="extract_snapshot_to_landing")
    def extract_snapshot_to_landing(source_config: dict[str, Any]) -> dict[str, Any]:
        context = get_current_context()
        run_dt = context["logical_date"].in_timezone("UTC")

        lake_bucket = Variable.get(
            "DATA_LAKE_BUCKET", default_var="nordic-peaks-oslo")
        service_account_json = Variable.get("GSHEETS_SERVICE_ACCOUNT_JSON")
        service_account_info = parse_service_account_json(service_account_json)

        source = source_config["source"]
        spreadsheet_id = source_config["spreadsheet_id"]
        worksheet_name = source_config["worksheet_name"]

        records = fetch_worksheet_records(
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
            service_account_info=service_account_info,
        )

        landing_key = build_landing_key(source=source, run_dt=run_dt)
        landing_uri = write_snapshot_to_s3_if_missing(
            records=records,
            bucket=lake_bucket,
            key=landing_key,
        )

        return {
            "source_config": source_config,
            "source": source,
            "row_count": len(records),
            "landing_uri": landing_uri,
            "year": run_dt.strftime("%Y"),
            "month": run_dt.strftime("%m"),
        }

    @task(task_id="transform_landing_to_processed")
    def transform_landing_to_processed(snapshot: dict[str, Any]) -> dict[str, Any]:
        context = get_current_context()
        run_dt = context["logical_date"].in_timezone("UTC")
        lake_bucket = Variable.get(
            "DATA_LAKE_BUCKET", default_var="nordic-peaks-oslo")

        source_config = snapshot["source_config"]
        source = snapshot["source"]
        landing_uri = snapshot["landing_uri"]

        records = read_snapshot_from_s3(landing_uri)
        dataframe, athena_types = records_to_typed_dataframe(
            records=records,
            source_config=source_config,
        )

        processed_key = build_processed_key(source=source, run_dt=run_dt)
        processed_uri = write_processed_parquet(
            dataframe=dataframe,
            bucket=lake_bucket,
            key=processed_key,
            athena_types=athena_types,
        )

        return {
            "source": source,
            "row_count": len(dataframe),
            "landing_uri": landing_uri,
            "processed_uri": processed_uri,
            "year": snapshot["year"],
            "month": snapshot["month"],
        }

    @task(task_id="log_result")
    def log_result(result: dict[str, Any]) -> None:
        print(
            "Google Sheets medallion pipeline complete: "
            f"source={result['source']}, "
            f"rows={result['row_count']}, "
            f"landing={result['landing_uri']}, "
            f"processed={result['processed_uri']}, "
            f"partition={result['year']}-{result['month']}"
        )

    sources = load_sources()
    landing_snapshots = extract_snapshot_to_landing.expand(
        source_config=sources)
    processed_results = transform_landing_to_processed.expand(
        snapshot=landing_snapshots)
    log_result.expand(result=processed_results)


dag = google_sheets_extract_dag()
