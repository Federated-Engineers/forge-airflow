from airflow.sdk import DAG
from pendulum import datetime
from datetime import timedelta
from airflow.providers.standard.operators.python import PythonOperator
from business_logic.glaciair_logic import load_gsheets_s3_csv


DAG_ID = 'oslo-project-dag'

default_args = {
    'owner': 'Federated-Engineers',
    'depends_on_past': False,
    'start_date': datetime(2021, 11, 15),
    'retries': 0,
    'retry_delay': timedelta(seconds=5),
    'execution_timeout': timedelta(minutes=10)
}

with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    schedule='@daily',
    catchup=False,
    tags=['Forge']
):

    run_pipeline = PythonOperator(
        task_id='load_gsheet_s3',
        python_callable=load_gsheets_s3_csv,
        op_kwargs={
            "report_date": '{{ ds }}'
        }
    )
