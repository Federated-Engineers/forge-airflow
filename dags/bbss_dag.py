from datetime import timedelta

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from pendulum import datetime

from business_logic.bbss.task import analytics_task, extract_task, transform_task

default_args = {
    "owner": "Federated_engineers",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="bbss_weather_pipeline",
    description="BBSS SafePass Daily Weather Pipeline",
    start_date=datetime(2026, 7, 12),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["bbss", "weather"],
) as dag:

    extract = PythonOperator(
        task_id="extract_weather_data",
        python_callable=extract_task,
    )

    transform = PythonOperator(
        task_id="transform_weather_data",
        python_callable=transform_task,
    )

    analytics = PythonOperator(
        task_id="build_weather_analytics",
        python_callable=analytics_task,
    )

    extract >> transform >> analytics
