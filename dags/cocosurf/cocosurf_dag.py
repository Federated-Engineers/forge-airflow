import logging
from datetime import timedelta
import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from dags.cocosurf.copy_into_raw import COPY_INTO_RAW

logger = logging.getLogger(__name__)

default_args = {
    "owner": "Federated-Engineers",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),

}

with DAG(
    dag_id="cocosurf_dbt_pipeline",
    description="Ingest Cocosurf data into Snowflake and run dbt on ECS Fargate",
    start_date=pendulum.datetime(2026, 5, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
) as dag:

    network_config = Variable.get(
        "cocosurf_dbt_network",
        default_var={
            "subnets": [
                "subnet-0613b8ccd258f4cca",
                "subnet-0af2d376a426b58bb",
            ],
            "securityGroups": ["sg-031991a3af44f3441"],
            "assignPublicIp": "ENABLED",
        },
        deserialize_json=True,
    )

    ingest_s3_to_snowflake = SQLExecuteQueryOperator(
        task_id="ingest_s3_to_snowflake",
        conn_id="snowflake_cocosurf",
        sql=COPY_INTO_RAW,
        split_statements=True,
        show_return_value_in_logs=True,
    )

    run_cocosurf_dbt = EcsRunTaskOperator(
        task_id="run_cocosurf_dbt",
        cluster="cocosurf-dbt-cluster",
        task_definition="cocosurf-dbt",
        launch_type="FARGATE",
        platform_version="LATEST",
        aws_conn_id="aws_default",
        region="eu-central-1",
        network_configuration={
            "awsvpcConfiguration": network_config,
        },

        overrides={
            "containerOverrides": [
                {
                    "name": "cocosurf-dbt",
                    "command": ["build"],
                }
            ]
        },
        reattach=True,
        wait_for_completion=True,
        deferrable=True,
    )

    ingest_s3_to_snowflake >> run_cocosurf_dbt
