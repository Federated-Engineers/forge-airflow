from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from pendulum import datetime

from business_logic.linen_luxury.main import run_all_scripts

dag = DAG(
    dag_id="Liffey_Linens_Insights",
    start_date=datetime(2026, 4, 22),
    schedule="0 */1 * * *",
    catchup=False,
)


run_etl_script_to_s3 = PythonOperator(
    task_id="run_all_scripts",
    python_callable=run_all_scripts,
    dag=dag
)

run_etl_script_to_s3
