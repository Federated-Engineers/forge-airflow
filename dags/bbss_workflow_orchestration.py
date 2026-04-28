from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from pendulum import datetime as pendulum_datetime

from business_logic.bbss_weather_forecast.tasks import (
    dump_raw_json, fetch, send_transformed_parquet, transform)
from plugins.slack_utils import slack_failure_alert, slack_success_alert

default_args = {
        "owner": "Federated Engineers",
        "retries": 2,
        "retry_delay": timedelta(seconds=100),
        "on_failure_callback": slack_failure_alert,
        "on_success_callback": slack_success_alert
    }

with DAG(
    dag_id="bbss_weather_forecast_ingestion_pipeline",
    schedule="0 23 * * *",
    start_date=pendulum_datetime(2026, 4, 23),
    catchup=False,
    default_args=default_args,
    tags=["Federated Engineers", "forge", "weather", "calvia"],
) as dag:

    fetch_task = PythonOperator(
        task_id='_fetch',
        python_callable=fetch
    )

    dump_raw_json_task = PythonOperator(
        task_id='_dump_raw',
        python_callable=dump_raw_json
    )

    transform_task = PythonOperator(
        task_id='_transform',
        python_callable=transform
    )

    send_transformed_parquet_task = PythonOperator(
        task_id='_send_parquet',
        python_callable=send_transformed_parquet
    )

    (
        fetch_task
        >> dump_raw_json_task
        >> transform_task
        >> send_transformed_parquet_task
    )
