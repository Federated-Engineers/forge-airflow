"""
DAG for the Angel City Health System Pipeline.
"""

import logging
from typing import Any

from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk import Variable, dag
from pendulum import datetime, duration


default_args = {
    "owner": "federated_engineers",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": duration(minutes=1),
}


@dag(
    dag_id="angel_city_health_systems_dag",
    default_args=default_args,
    description="ACHS base pipeline: extract -> transform -> load",
    start_date=datetime(2026, 5, 19),
    end_date=datetime(2026, 5, 24),
    schedule="@daily",
    catchup=False,
    tags=["forge", "achs", "ecs", "snowflake", "dbt"],
)
def achs_dag():
    """To Do"""

    dag_variables: dict[str, Any] = Variable.get(
        "ACHS_DAG",
        deserialize_json=True
    )

    copy_into_table_template: str = """
    COPY INTO {database}.{schema}.{table}(
        RAW_DATA,
        SOURCE_FILE,
        FILE_ROW_NUMBER,
        LOADED_AT_TIMESTAMP
    )
    FROM (
        SELECT
            $1,
            METADATA$FILENAME,
            METADATA$FILE_ROW_NUMBER,
            CURRENT_TIMESTAMP()
        FROM @{database}.{schema}.{stage}/{entity}/{ds}/
    );
    """

    load_claims_to_landing = SQLExecuteQueryOperator(
        task_id="load_claims_to_landing",
        conn_id=dag_variables["snowflake_conn_id"],
        database=dag_variables["landing_db"],
        sql=copy_into_table_template.format(
            database=dag_variables["landing_db"],
            schema=dag_variables["landing_schema"],
            table=dag_variables["claim_landing_table"],
            stage=dag_variables["landing_files_stage"],
            entity="claims",
            ds="{{ ds }}"
        )
    )

    load_diagnoses_to_landing = SQLExecuteQueryOperator(
        task_id="load_diagnoses_to_landing",
        conn_id=dag_variables["snowflake_conn_id"],
        database=dag_variables["landing_db"],
        sql=copy_into_table_template.format(
            database=dag_variables["landing_db"],
            schema=dag_variables["landing_schema"],
            table=dag_variables["diagnoses_landing_table"],
            stage=dag_variables["landing_files_stage"],
            entity="diagnoses",
            ds="{{ ds }}"
        )
    )

    load_encounters_to_landing = SQLExecuteQueryOperator(
        task_id="load_encounters_to_landing",
        conn_id=dag_variables["snowflake_conn_id"],
        database=dag_variables["landing_db"],
        sql=copy_into_table_template.format(
            database=dag_variables["landing_db"],
            schema=dag_variables["landing_schema"],
            table=dag_variables["encounters_landing_table"],
            stage=dag_variables["landing_files_stage"],
            entity="encounters",
            ds="{{ ds }}"
        )
    )

    load_patients_to_landing = SQLExecuteQueryOperator(
        task_id="load_patients_to_landing",
        conn_id=dag_variables["snowflake_conn_id"],
        database=dag_variables["landing_db"],
        sql=copy_into_table_template.format(
            database=dag_variables["landing_db"],
            schema=dag_variables["landing_schema"],
            table=dag_variables["patients_landing_table"],
            stage=dag_variables["landing_files_stage"],
            entity="patients",
            ds="{{ ds }}"
        )
    )

    load_providers_to_landing = SQLExecuteQueryOperator(
        task_id="load_providers_to_landing",
        conn_id=dag_variables["snowflake_conn_id"],
        database=dag_variables["landing_db"],
        sql=copy_into_table_template.format(
            database=dag_variables["landing_db"],
            schema=dag_variables["landing_schema"],
            table=dag_variables["providers_landing_table"],
            stage=dag_variables["landing_files_stage"],
            entity="providers",
            ds="{{ ds }}"
        )
    )
    )

    load_claims_to_landing
    load_diagnoses_to_landing
    load_encounters_to_landing
    load_patients_to_landing
    load_providers_to_landing


achs_dag()
