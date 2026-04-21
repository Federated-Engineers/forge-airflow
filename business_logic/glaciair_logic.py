import json
import logging
from typing import Any

from airflow.sdk import Variable

from business_logic.integrations import _get_ssm_paramater, load_gsheet_to_s3

logger = logging.getLogger(__name__)


def _validate_variables() -> dict[str, Any]:
    """
    Retrieve and Validate the required Airflow Variables for \
        the Glaciair data pipeline.

    Returns:
        dict[str, Any]: A dictionary containing the validated variables.
    """
    glaciair_variables = Variable.get(
        "GLACIAIR_LOGISTICS",
        deserialize_json=True
    )

    ssm_parameter_name: str = glaciair_variables.get("ssm_parameter_name", "")
    s3_bucket: str = glaciair_variables.get("s3_bucket", "")
    s3_prefix: str = glaciair_variables.get("s3_prefix", "")

    # This expects a JSON list object in the Airflow Variable.
    spreadsheet_names: list[str] = glaciair_variables.get(
        "spreadsheet_names",
        []
    )
    if not isinstance(spreadsheet_names, list):
        raise ValueError("Spreadsheet names must be a JSON List.")
    else:
        for sheet_name in spreadsheet_names:
            if not isinstance(sheet_name, str):
                raise ValueError("Sheet names must be a string.")
    return {
        "ssm_parameter_name": ssm_parameter_name,
        "spreadsheet_names": spreadsheet_names,
        "s3_bucket": s3_bucket,
        "s3_prefix": s3_prefix
    }


def sync_glaciair_gsheets_to_s3(report_date: str) -> None:
    """
    Main Task Function to Sync Glaciair Google Sheets Data to S3.

    Args:
        report_date (str): The date for which the report is being generated.
    """

    glacair_variables = _validate_variables()
    num_airflow_variables: int = len(glacair_variables)
    logger.info(
        f"Validated {num_airflow_variables} GlaciAir Airflow Variables"
    )

    num_spreadsheets: int = len(glacair_variables["spreadsheet_names"])
    logger.info(
        f"Found {num_spreadsheets} Google Sheets to sync."
    )

    google_service_cred = _get_ssm_paramater(
        glacair_variables["ssm_parameter_name"]
    )
    logger.info(
        "Retrieved Google Service Account credentials from SSM Parameter."
    )

    for i, gsheet_name in enumerate(
        glacair_variables["spreadsheet_names"],
        start=1
    ):
        logger.info(
            f"{i}/{num_spreadsheets} ... "
            f"Starting Glaciair GSheets to S3 Sync for Sheet: {gsheet_name!r}"
        )

        load_gsheet_to_s3(
            gsheet_name=gsheet_name,
            s3_bucket=glacair_variables["s3_bucket"],
            s3_prefix=glacair_variables["s3_prefix"],
            service_credentials=json.loads(
                google_service_cred["Parameter"]["Value"]
            ),
            format="parquet"
        )
