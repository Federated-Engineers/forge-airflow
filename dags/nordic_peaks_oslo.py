import datetime
from typing import Any

from airflow.sdk import Variable, dag, get_current_context, task

from business_logic.nordic_peaks.extract_to_s3 import (validate_metadata,
                                                       write_raw_to_s3)
from business_logic.nordic_peaks.load_processed import load_data
from business_logic.nordic_peaks.transform import transform_data
from plugins.AWS.aws_wrangler.S3.wrangler_read import read_csv_data
from plugins.gspread_auth import get_google_sheets_data

DAG_ID = "NordicPeaks_GoogleSheets_Pipeline"


@dag(
    dag_id=DAG_ID,
    start_date=datetime.datetime(2026, 7, 20),
    schedule="0 1 * * *",
    catchup=False,
    tags=["google-sheets", "nordic-peaks"],
    max_active_runs=1,
)
def start_nordic_peaks_pipeline():
    @task(task_id="load_and_validate_gsheet_metadata")
    def load_and_validate_gsheet_metadata() -> list[dict[str, Any]]:
        gsheet_source_metadata = Variable.get("GSHEETS_SOURCES",
                                              deserialize_json=True)
        source_metadata = validate_metadata(gsheet_source_metadata)
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
        landing_zone_path = write_raw_to_s3(
            records=dataframe,
            bucket=lake_bucket,
            run_datetime=run_datetime,
            gsheet_source=source,
        )

        return {
            "source_config": source_config,
            "source": source,
            "raw_data_path": landing_zone_path,
            "year": run_datetime.strftime("%Y"),
            "month": run_datetime.strftime("%m"),
            "day": run_datetime.strftime("%d"),
        }

    @task(task_id="transform_raw_data")
    def transform_raw_data(
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        source_config = raw_payload["source_config"]
        source = raw_payload["source"]
        raw_data_path = raw_payload["raw_data_path"]

        dataframe, semantic_types = transform_data(
            raw_data_path,
            source_config={**source_config, "source": source},
        )

        return {
            "source": raw_payload["source"],
            "row_count": len(dataframe),
            "landing_uri": raw_data_path,
            "semantic_types": semantic_types,
            "year": raw_payload["year"],
            "month": raw_payload["month"],
            "day": raw_payload["day"],
            "partition_date_column": source_config[
                "partition_date_column"
            ],
        }

    @task(task_id="load_transformed_data")
    def load_transformed_data(transformed_payload: dict[str, Any],):

        load_data(
            dataframe=read_csv_data(transformed_payload["landing_uri"]),
            bucket=Variable.get("DATA_LAKE_BUCKET"),
            semantic_types=transformed_payload["semantic_types"],
            source=transformed_payload["source"],
            partition_date_column=transformed_payload[
                "partition_date_column"
            ],
        )

    sources = load_and_validate_gsheet_metadata()
    landing_snapshots = extract_source_to_aws_landing_zone.expand(
        source_config=sources
    )
    transformed_data = transform_raw_data.expand(
        raw_payload=landing_snapshots
    )
    load_transformed_data.expand(transformed_payload=transformed_data)


dag = start_nordic_peaks_pipeline()
