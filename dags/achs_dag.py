"""
Base DAG for the ACHS pipeline.
"""

from airflow.sdk import dag, task, Variable
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime, duration

# Airflow-level defaults shared by every task in this DAG.
default_args = {
    "owner": "federated_engineers",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": duration(minutes=1),
}


@dag(
    dag_id="achs_pipeline",
    default_args=default_args,
    description="ACHS base pipeline: extract -> transform -> load",
    start_date=datetime(2026, 5, 19),
    end_date=datetime(2026, 5, 24),
    schedule="@daily",
    catchup=False,
    tags=["forge", "achs"],
)
def achs_pipeline():
    """TaskFlow-style pipeline. Replace the placeholder bodies with real logic."""

    variables = Variable.get("ACHS", deserialize_json=True)

    load_claims_to_landing = SQLExecuteQueryOperator(
        task_id="load_claims_to_landing",
        conn_id=variables["snowflake_conn_id"],
        database=variables["claim_lnd_db"],
        sql="""
        COPY INTO {database}.{schema}.{table}(
            RAW_DATA,
            SOURCE_FILE,
            FILE_ROW_NUMBER,
            LOADED_AT_TIMESTAMP
        )
        FROM (
            SELECT
                claims.$1,
                METADATA$FILENAME,
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM @{database}.{schema}.{stage}/claims/{ds}/ claims
        );
        """.format(
            database = variables["claim_lnd_db"],
            schema = variables["claim_lnd_schema"],
            table = variables["claim_lnd_table"],
            stage = variables["lnd_stage"],
            ds = "{{ ds }}"
        )
    )

    load_diagnoses_to_landing = SQLExecuteQueryOperator(
        task_id="load_diagnoses_to_landing",
        conn_id=variables["snowflake_conn_id"],
        database=variables["claim_lnd_db"],
        sql="""
        COPY INTO {database}.{schema}.{table}(
            RAW_DATA,
            SOURCE_FILE,
            FILE_ROW_NUMBER,
            LOADED_AT_TIMESTAMP
        )
        FROM (
            SELECT
                diagnoses.$1,
                METADATA$FILENAME,
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM @{database}.{schema}.{stage}/diagnoses/{ds}/ diagnoses
        );
        """.format(
            database = variables["claim_lnd_db"],
            schema = variables["claim_lnd_schema"],
            table = variables["claim_lnd_table"],
            stage = variables["lnd_stage"],
            ds = "{{ ds }}"
        )
    )

    load_encounters_to_landing = SQLExecuteQueryOperator(
        task_id="load_encounters_to_landing",
        conn_id=variables["snowflake_conn_id"],
        database=variables["claim_lnd_db"],
        sql="""
        COPY INTO {database}.{schema}.{table}(
            RAW_DATA,
            SOURCE_FILE,
            FILE_ROW_NUMBER,
            LOADED_AT_TIMESTAMP
        )
        FROM (
            SELECT
                encounters.$1,
                METADATA$FILENAME,
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM @{database}.{schema}.{stage}/encounters/{ds}/ encounters
        );
        """.format(
            database = variables["claim_lnd_db"],
            schema = variables["claim_lnd_schema"],
            table = variables["claim_lnd_table"],
            stage = variables["lnd_stage"],
            ds = "{{ ds }}"
        )
    )

    load_patients_to_landing = SQLExecuteQueryOperator(
        task_id="load_patients_to_landing",
        conn_id=variables["snowflake_conn_id"],
        database=variables["claim_lnd_db"],
        sql="""
        COPY INTO {database}.{schema}.{table}(
            RAW_DATA,
            SOURCE_FILE,
            FILE_ROW_NUMBER,
            LOADED_AT_TIMESTAMP
        )
        FROM (
            SELECT
                patients.$1,
                METADATA$FILENAME,
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM @{database}.{schema}.{stage}/patients/{ds}/ patients
        );
        """.format(
            database = variables["claim_lnd_db"],
            schema = variables["claim_lnd_schema"],
            table = variables["claim_lnd_table"],
            stage = variables["lnd_stage"],
            ds = "{{ ds }}"
        )
    )

    load_providers_to_landing = SQLExecuteQueryOperator(
        task_id="load_providers_to_landing",
        conn_id=variables["snowflake_conn_id"],
        database=variables["claim_lnd_db"],
        sql="""
        COPY INTO {database}.{schema}.{table}(
            RAW_DATA,
            SOURCE_FILE,
            FILE_ROW_NUMBER,
            LOADED_AT_TIMESTAMP
        )
        FROM (
            SELECT
                providers.$1,
                METADATA$FILENAME,
                METADATA$FILE_ROW_NUMBER,
                CURRENT_TIMESTAMP()
            FROM @{database}.{schema}.{stage}/providers/{ds}/ providers
        );
        """.format(
            database = variables["claim_lnd_db"],
            schema = variables["claim_lnd_schema"],
            table = variables["claim_lnd_table"],
            stage = variables["lnd_stage"],
            ds = "{{ ds }}"
        )
    )

    load_claims_to_landing
    load_diagnoses_to_landing
    load_encounters_to_landing
    load_patients_to_landing
    load_providers_to_landing

achs_pipeline()
