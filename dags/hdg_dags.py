from datetime import timedelta

import pendulum
from airflow.decorators import task
from airflow.sdk import DAG, Variable

from business_logic.HDG.google_sheet_extractor import extract_google_sheet
from business_logic.HDG.load_s3_athena import (load_raw_data_to_s3,
                                               move_parquet_to_cleaned_folder)
from business_logic.HDG.transform_dfs import transform_dfs


start_date = pendulum.datetime(
    2026,
    8,
    12,
    tz="Europe/Berlin",
)

config = Variable.get(
    "hdg_json",
    deserialize_json=True,
)

s3_bucket = config.get("s3_bucket_name")
athena_db = config.get("athena_db")
lancy_id = config.get("lancy_id")
rhones_id = config.get("rhones_id")


default_args = {
    "owner": "airflow",
    "start_date": start_date,
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}




with DAG(
    dag_id="hdg-dags",
    default_args=default_args,
    start_date=start_date,
    schedule="0 0 * * *",
    catchup=False,
    tags=["hdg"],
) as dag:

    # =====================================================
    # 1. EXTRACT
    # =====================================================

    @task(task_id="get_lancy_data")
    def get_lancy_data_task():
        return extract_google_sheet(sheet_id=lancy_id)

    @task(task_id="get_rhone_data")
    def get_rhone_data_task():
        return extract_google_sheet(sheet_id=rhones_id)



    @task(task_id="raw_data_to_s3_lancy")
    def raw_data_to_s3_lancy_task(df):
        return load_raw_data_to_s3(
            df=df,
            key="lancy.parquet",
        )

    @task(task_id="raw_data_to_s3_rhone")
    def raw_data_to_s3_rhone_task(df):
        return load_raw_data_to_s3(
            df=df,
            key="rhone.parquet",
        )



    @task(
        task_id="transform_data",
        multiple_outputs=True,
    )
    def transform_data_task(
        lancy_parquet,
        rhone_parquet,
    ):
        return transform_dfs(
            lancy_parquet,
            rhone_parquet,
        )



    @task(task_id="move_to_cleaned_folder_lancy")
    def move_to_cleaned_folder_lancy_task(df):

        return move_parquet_to_cleaned_folder(
            df=df,
            path_file=(f"s3://{s3_bucket}/" "cleaned_files/lancy.parquet"),
            tablename="lancy_data",
            partition_cols=["month"],
        )

    @task(task_id="move_to_cleaned_folder_rhone")
    def move_to_cleaned_folder_rhone_task(df):

        return move_parquet_to_cleaned_folder(
            df=df,
            path_file=(f"s3://{s3_bucket}/" "cleaned_files/rhone.parquet"),
            tablename="rhone_data",
            partition_cols=["month"],
        )



    lancy_df = get_lancy_data_task()
    rhone_df = get_rhone_data_task()

 

    raw_lancy = raw_data_to_s3_lancy_task(lancy_df)

    raw_rhone = raw_data_to_s3_rhone_task(rhone_df)


    transformed = transform_data_task(
        raw_lancy,
        raw_rhone,
    )


    move_to_cleaned_folder_lancy_task(transformed["lancy"])

    move_to_cleaned_folder_rhone_task(transformed["rhone"])
