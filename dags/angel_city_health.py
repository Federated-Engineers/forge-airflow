from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from business_logic.angel_city_health.extract import (
    copy_patients_data,
    copy_providers_data,
    copy_claims_data,
    copy_diagnoses_data,
    copy_encounters_data,
)

DAG_ID = "Angel_City_Health_System_Pipeline"

# Define default arguments
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    DAG_ID,
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:
    # Load Patients Data Task
    copy_patients_task = PythonOperator(
        task_id='load_patients_raw',
        python_callable=copy_patients_data,
    )

    # Load Providers Data Task
    copy_providers_task = PythonOperator(
        task_id='load_providers_raw',
        python_callable=copy_providers_data,
    )

    # Load Claims Data Task
    copy_claims_task = PythonOperator(
        task_id='load_claims_raw',
        python_callable=copy_claims_data,
    )

    # Load Diagnoses Data Task
    copy_diagnoses_task = PythonOperator(
        task_id='load_diagnoses_raw',
        python_callable=copy_diagnoses_data,
    )

    # Load Encounters Data Task
    copy_encounters_task = PythonOperator(
        task_id='load_encounters_raw',
        python_callable=copy_encounters_data,
    )

    # # Define task dependencies
    copy_patients_task >> copy_providers_task >> copy_claims_task >> copy_diagnoses_task >> copy_encounters_task
