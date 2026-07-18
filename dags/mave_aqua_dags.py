import awswrangler as wr
import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator
from business_logic.mave_aqua.load_data_s3 import move_file_and_register_athena
from business_logic.mave_aqua.transform import (clean_harvest_data,
                                                clean_lagoon_data)

import bypass_ray

_ = bypass_ray
# Ensure that awswrangler uses the correct
# engine for reading/writing Parquet files
wr.config.engine = "python"

start_date = pendulum.datetime(
    2026, 7, 13, tz="Europe/Berlin"
    )
config = Variable.get("var_json", deserialize_json=True)
s3_bucket = config.get("s3_bucket_name")
athena_db = config.get("athena_db")


default_args = {
    "owner": "airflow",
    "start_date": start_date,
}

with DAG(
    dag_id="mave-aqua-dags",
    default_args=default_args,
    start_date=start_date,
    schedule="0 0 * * *",
    catchup=False,
) as dag:

    extract_lagoon_data = SqlToS3Operator(
        task_id="lagoon_data_to_s3",
        sql_conn_id="supabase_postgres",
        query="SELECT * FROM historical.lagoon_environmental_log;",
        s3_bucket=s3_bucket,
        s3_key="raw_files/{{ ds }}/lagoon_environmental_log.parquet",
        replace=True,
        file_format="parquet",
    )

    extract_harvest_data = SqlToS3Operator(
        task_id="harvest_data_to_s3",
        sql_conn_id="supabase_postgres",
        query="SELECT * FROM historical.harvest_lifecycle_record;",
        s3_bucket=s3_bucket,
        s3_key="raw_files/{{ ds }}/harvest_lifecycle_record.parquet",
        replace=True,
        file_format="parquet",
    )

    @task
    def transform_harvest_data(ds=None):
        raw_s3_path = (
            f"s3://{s3_bucket}/raw_files/{ds}/"
            "harvest_lifecycle_record.parquet"
        )
        import awswrangler as wr

        wr.config.engine = "python"
        raw_harvest_data = wr.s3.read_parquet(raw_s3_path)
        cleaned_harvest_df = clean_harvest_data(raw_harvest_data)
        cleaned_harvest_df["extraction_date"] = ds
        return cleaned_harvest_df

    @task
    def transform_lagoon_data(ds=None):
        raw_s3_path = (
            f"s3://{s3_bucket}/raw_files/{ds}/"
            "lagoon_environmental_log.parquet"
        )
        import awswrangler as wr
        wr.config.engine = "python"

        raw_lagoon_data = wr.s3.read_parquet(raw_s3_path)
        cleaned_lagoon_df = clean_lagoon_data(raw_lagoon_data)
        cleaned_lagoon_df["extraction_date"] = ds
        return cleaned_lagoon_df

    @task
    def move_cleaned_harvest_and_register_to_athena(cleaned_harvest_df, ds=None):
        move_file_and_register_athena(
            df=cleaned_harvest_df,
            key=f"cleaned_and_partitioned/harvest_lifecycle_record/{ds}/",
            tablename="harvest_lifecycle_record",
            partition_cols=[
                "batch_type",
                ],
        )

    @task
    def move_cleaned_lagoon_and_register_to_athena(cleaned_lagoon_df, ds=None):
        move_file_and_register_athena(
            df=cleaned_lagoon_df,
            key=f"cleaned_and_partitioned/lagoon_environmental_log/{ds}/",
            tablename="lagoon_environmental_log",
            partition_cols=[
                "station_id",
                ],
        )

    # 1. Connect the Lagoon Pipeline
    lagoon_output = transform_lagoon_data()
    (
        extract_lagoon_data
        >> lagoon_output
        >> move_cleaned_lagoon_and_register_to_athena(lagoon_output)
    )

    # 2. Connect the Harvest Pipeline
    harvest_output = transform_harvest_data()
    (
        extract_harvest_data
        >> harvest_output
        >> move_cleaned_harvest_and_register_to_athena(harvest_output)
    )
