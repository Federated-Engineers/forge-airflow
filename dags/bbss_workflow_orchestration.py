from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from pendulum import datetime as pendulum_datetime

from business_logic.bbss_weather_forecast.tasks import fetch, send_as_parquet

default_args = {
        "owner": "Federated Engineers",
        "retries": 2,
        "retry_delay": timedelta(seconds=100),
    }

with DAG(
    dag_id="bbss_weather_forecast_ingestion_pipeline",
    schedule="30 10 * * *",
    start_date=pendulum_datetime(2026, 4, 30),
    catchup=True,
    default_args=default_args,
    tags=["Federated Engineers", "forge", "weather", "calvia"],
) as dag:

    fetch_task = PythonOperator(
        task_id='_fetch',
        python_callable=fetch
    )

    send_parquet_task = PythonOperator(
        task_id='_send_parquet',
        python_callable=send_as_parquet
    )

    fetch_task.set_downstream(send_parquet_task)
