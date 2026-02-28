import datetime

import awswrangler as wr
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

DAG_ID = 'latest-demo'


# simple task to test full flow
def demo():
    wr.s3.to_parquet(
        df=pd.DataFrame({'col': [1, 2, 5]}),
        path='s3://poc-bucket-oremeta/prefix/my_file.parquet')
    return "Data written to s3."


default_args = {
    'owner': 'Federated-Engineers',
    'depends_on_past': False,
    'start_date': datetime.datetime(2021, 11, 15),
    'retries': 3,
    'retry_delay': datetime.timedelta(seconds=5),
    'execution_timeout': datetime.timedelta(minutes=10)
}


dag = DAG(
    DAG_ID,
    default_args=default_args,
    # schedule_interval='13 8,18 * * 1-6',
    max_active_runs=1,
    catchup=False,
    tags=[DAG_ID]
)


get_latest_report_file_task = PythonOperator(
    dag=dag,
    task_id='get_latest_report_file',
    python_callable=demo
)
