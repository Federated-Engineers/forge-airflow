import datetime
from typing import Any

from airflow.sdk import Variable, dag, get_current_context, task

from business_logic.nordic_peaks.extract_to_s3 import (get_google_sheets_data,
                                                       validate_metadata,
                                                       write_raw_json_to_s3)
from business_logic.nordic_peaks.load_processed import write_processed_parquet
from business_logic.nordic_peaks.read_raw_data import read_raw_data_from_s3
from business_logic.nordic_peaks.s3_keys import (build_landing_key,
                                                 build_processed_key)
from business_logic.nordic_peaks.transform import \
    transform_data_to_typed_dataframe

DAG_ID = "NordicPeaks_GoogleSheets_Pipeline"


@dag(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2024, 1, 1),
    schedule="0 * * * *",
    catchup=False,
    tags=["google-sheets", "nordic-peaks"],
    max_active_runs=1,
)
# Extract Google Sheets data, transform to canonical schema,
# and write to S3 landing and processed zones.
def start_nordic_peaks_pipeline():
    @task(task_id="load_and_validate_sources")
    def load_and_validate_sources() -> list[dict[str, Any]]:
        sources = Variable.get("GSHEETS_SOURCES", deserialize_json=True)
        source_metadata = validate_metadata(sources)
        return source_metadata

    @task(task_id="extract_source_to_aws_landing_zone")
    def extract_source_to_aws_landing_zone(
        source_config: dict[str, Any],
    ) -> dict[str, Any]:
        context = get_current_context()
        run_datetime = context["logical_date"].in_timezone("UTC")
        lake_bucket = Variable.get("DATA_LAKE_BUCKET")

        source = source_config["source_id"]
        spreadsheet_id = source_config["spreadsheet_id"]
        worksheet_name = source_config["worksheet_name"]

        dataframe = get_google_sheets_data(
            gsheet_id=spreadsheet_id,
            sheet_name=worksheet_name,
        )

        # Convert dataframe to row-wise dictionaries for JSON snapshot writes.
        records = dataframe.to_dict(orient="records")

        landing_key = build_landing_key(source=source, run_dt=run_datetime)
        landing_uri = write_raw_json_to_s3(
            records=records,
            bucket=lake_bucket,
            key=landing_key,
        )

        return {
            "source_config": source_config,
            "source": source,
            "row_count": len(records),
            "landing_uri": landing_uri,
            "year": run_datetime.strftime("%Y"),
            "month": run_datetime.strftime("%m"),
            "day": run_datetime.strftime("%d"),
        }

    # Read landing snapshot, validate and type, then write processed Parquet.
    @task(task_id="transform_landing_to_processed")
    def transform_raw_to_processed_zone(
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        lake_bucket = Variable.get("DATA_LAKE_BUCKET")
        source_config = raw_payload["source_config"]
        source = raw_payload["source"]
        landing_uri = raw_payload["landing_uri"]

        raw_data = read_raw_data_from_s3(landing_uri)
        # Transform to canonical dataframe plus semantic type map
        # used by the Parquet writer.
        dataframe, semantic_types = transform_data_to_typed_dataframe(
            raw_data,
            source_config={**source_config, "source": source},
        )

        processed_key = build_processed_key()
        processed_uri = write_processed_parquet(
            dataframe=dataframe,
            bucket=lake_bucket,
            key=processed_key,
            semantic_types=semantic_types,
            source=source,
            partition_date_column=source_config[
                "partition_date_column"
            ],
        )

        return {
            "source": source,
            "row_count": len(dataframe),
            "landing_uri": landing_uri,
            "processed_uri": processed_uri,
            "year": raw_payload["year"],
            "month": raw_payload["month"],
            "day": raw_payload["day"],
            "partition_date_column": source_config[
                "partition_date_column"
            ],
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

    sources = load_and_validate_sources()
    # Dynamic mapping creates one task instance per source config.
    landing_snapshots = extract_source_to_aws_landing_zone.expand(
        source_config=sources
    )
    processed_results = transform_raw_to_processed_zone.expand(
        raw_payload=landing_snapshots
    )
    log_result.expand(result=processed_results)


dag = start_nordic_peaks_pipeline()
