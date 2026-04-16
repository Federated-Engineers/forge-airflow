import datetime
from typing import Any
from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from business_logic.glaciair_logic import load_gsheets_s3_csv

################################## Airflow Variables used in DAG ##################################
# GLACIAIR_S3_PATH
# GLACIAIR_SPREADSHEETS
# GLACIAIR_SSM_PARAMETER
###################################################################################################

DAG_ID: str = "glaciair-logistics-data-sync"
DEFAULT_ARGS: dict[str, Any] = {
	"owner": "Federated-Engineers",
	"depends_on_past": False,
	"start_date": datetime.datetime(2026, 1, 1),
	"retries": 3,
	"retry_delay": datetime.timedelta(minutes=1),
	"execution_timeout": datetime.timedelta(minutes=10),
}

with DAG(
	dag_id=DAG_ID,
	default_args=DEFAULT_ARGS,
	schedule="@daily",
	max_active_runs=1,
	catchup=False,
	tags=["forge", "data-sync", "glaciair"],
):
	run_pipeline = PythonOperator(
        task_id='load_gsheet_to_s3',
        python_callable=load_gsheets_s3_csv,
        op_kwargs={
            "report_date": '{{ ds }}'
        }
    )
