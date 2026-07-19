import datetime
from typing import Any

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.sdk import get_current_context

from business_logic.nordic_peaks.landing import (
    read_snapshot_from_s3,
    write_snapshot_to_s3_if_missing,
)
from business_logic.nordic_peaks.processed import write_processed_parquet
from business_logic.nordic_peaks.s3_keys import (
    build_landing_key,
    build_processed_key,
)
from business_logic.nordic_peaks.transform import records_to_typed_dataframe
from plugins.gspread_auth import GOOGLE_CREDS_SSM_PATH, get_data

DAG_ID = "NordicPeaks_GoogleSheets_Pipeline"


@dag(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2024, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["google-sheets", "ingestion"],
    max_active_runs=1,
)
# Extract Google Sheets data, transform to canonical schema, and write to S3 landing and processed zones.
def google_sheets_extract_dag():
    @task(task_id="load_sources")
    def load_sources() -> list[dict[str, Any]]:
        sources = Variable.get("GSHEETS_SOURCES", deserialize_json=True)
        if not isinstance(sources, list) or not sources:
            raise ValueError("GSHEETS_SOURCES must be a non-empty JSON array")

        required_fields = {
            "source_id",
            "spreadsheet_id",
            "worksheet_name",
            "partition_date_column",
        }
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

    @task(task_id="extract_source_snapshot_to_aws_landing_zone")
    def extract_snapshot_to_landing(source_config: dict[str, Any]) -> dict[str, Any]:
        context = get_current_context()
        run_dt = context["logical_date"].in_timezone("UTC")

        lake_bucket = Variable.get(
            "DATA_LAKE_BUCKET", default_var="nordic-peaks-oslo")
        creds_ssm_path = Variable.get(
            "GSHEETS_CREDS_SSM_PATH", default_var=GOOGLE_CREDS_SSM_PATH)

        source = source_config["source_id"]
        spreadsheet_id = source_config["spreadsheet_id"]
        worksheet_name = source_config["worksheet_name"]

        dataframe = get_data(
            gsheet_id=spreadsheet_id,
            ssm_path=creds_ssm_path,
            sheet_name=worksheet_name,
        )
        records = dataframe.to_dict(orient="records")

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
            "day": run_dt.strftime("%d"),
        }
    # transform_landing_to_processed task: read landing snapshot, validate and type, write to processed Parquet.

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
        # Transform to canonical dataframe + semantic type map for Parquet write.
        dataframe, semantic_types = records_to_typed_dataframe(
            records=records,
            source_config={**source_config, "source": source},
        )

        processed_key = build_processed_key()
        processed_uri = write_processed_parquet(
            dataframe=dataframe,
            bucket=lake_bucket,
            key=processed_key,
            semantic_types=semantic_types,
            source=source,
            partition_date_column=source_config["partition_date_column"],
        )

        return {
            "source": source,
            "row_count": len(dataframe),
            "landing_uri": landing_uri,
            "processed_uri": processed_uri,
            "year": snapshot["year"],
            "month": snapshot["month"],
            "day": snapshot["day"],
            "partition_date_column": source_config["partition_date_column"],
        }

    @task(task_id="log_result")
    def log_result(result: dict[str, Any]) -> None:
        print(
            "Google Sheets medallion pipeline complete: "
            f"source={result['source']}, "
            f"rows={result['row_count']}, "
            f"landing={result['landing_uri']}, "
            f"processed={result['processed_uri']}, "
            f"partition_date_column={result['partition_date_column']}"
        )

    sources = load_sources()
    landing_snapshots = extract_snapshot_to_landing.expand(
        source_config=sources)
    processed_results = transform_landing_to_processed.expand(
        snapshot=landing_snapshots)
    log_result.expand(result=processed_results)


dag = google_sheets_extract_dag()
