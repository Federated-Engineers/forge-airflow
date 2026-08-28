import logging

import dlt
from airflow.hooks.base import BaseHook
from airflow.sdk import Variable, dag, task
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_database

DAG_ID: str = "luminabricks_historical_load"


@dag(
    dag_id=DAG_ID,
    description="""
    Ingests data from Postgres tables on SupaBase server into an S3 Bucket
    """,
    schedule=None,  # this would be manually trigerred
    max_active_runs=1,
)
def historical_data_load():

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    @task(
        task_id="postgres_tables_to_s3",
        show_return_value_in_logs=True,
        do_xcom_push=False,
    )
    def ingest_postgres_tables_to_s3():

        variables: dict = Variable.get(
            "LUMINABRICKS_HISTORICAL_INGEST", deserialize_json=True
        )
        conn = BaseHook.get_connection("LUMINABRICKS_POSTGRES_CONNECTION")

        credentials = ConnectionStringCredentials(
            "postgresql+psycopg2://"
            f"{conn.login}:{conn.password}"
            f"@{conn.host}:{conn.port}/{conn.schema}"
        )

        source = sql_database(
            credentials,
            schema=variables["schema"],
            table_names=variables["table_names"],
        )

        pipeline = dlt.pipeline(
            pipeline_name=DAG_ID,
            destination=dlt.destinations.filesystem(
                bucket_url="s3://{}/{}".format(
                    variables["destination_bucket"],
                    variables["destination_path"],
                )
            ),
        )

        load_info = pipeline.run(
            source, loader_file_format="parquet", write_disposition="replace"
        )

        logging.info("Load info: %s", load_info)

    ingest_postgres_tables_to_s3()


historical_data_load()
