from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.providers.standard.operators.python import PythonOperator

from business_logic.angel_city_health.extract import (copy_claims_data,
                                                      copy_diagnoses_data,
                                                      copy_encounters_data,
                                                      copy_patients_data,
                                                      copy_providers_data)

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

    # run ECS task
    run_dbt_transformations = EcsRunTaskOperator(
        task_id="run_dbt_transformations",
        cluster="achs-data-cluster",
        task_definition="achs-dbt-task",
        launch_type='FARGATE',
        network_configuration={'awsvpcConfiguration': {
            'subnets': [
                'subnet-0737ad770665b10e0',
                'subnet-098298f12f873b1de',
                'subnet-0dbc6bd9c895e291a',
            ],
            'securityGroups': ['sg-0b65fc4de73b84f1a', 'sg-045d45c5be9b26ab9'],
            'assignPublicIp': 'ENABLED'
        }},
        overrides={
            "containerOverrides": [
                {
                    "name": "dbt-container",
                    "command": ["dbt", "build", "--profiles-dir", "."]
                }
            ]
        },
        awslogs_group='/ecs/achs-dbt',
        awslogs_region='eu-central-1',
        awslogs_stream_prefix="dbt",
    )

    # # Define task dependencies
    [copy_patients_task,
     copy_providers_task,
     copy_claims_task,
     copy_diagnoses_task,
     copy_encounters_task
     ] >> run_dbt_transformations
