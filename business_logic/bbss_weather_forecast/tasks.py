from datetime import date, timedelta

from airflow.sdk import Variable

from business_logic.bbss_weather_forecast.ingestion_pipeline import (get_forecast,
                                                           send_parquet_to_s3)
from plugins.aws import hive_partitioned_bucket_setup

bbss_s3_bucket = Variable.get("BUCKET_NAME")


def fetch(**context):
    ds = context["ds"]
    execution_date = date.fromisoformat(ds)
    target_date = execution_date + timedelta(days=1)
    
    nextday_forecast = get_forecast(target_date)
    
    context['ti'].xcom_push(key='nextday_forecast', value=nextday_forecast)
    context['ti'].xcom_push(key='target_date', value=str(target_date))


def send_as_parquet(**context):
    ti = context['ti']
    nextday_forecast = ti.xcom_pull(key='nextday_forecast', task_ids='_fetch')
    target_date = ti.xcom_pull(key='target_date', task_ids='_fetch')

    bucket_name = bbss_s3_bucket
    
    date_str = str(target_date)
    stripped_dt = date_str.replace('-', '')
    key = hive_partitioned_bucket_setup("bbss_forecast", date_str)
    send_parquet_to_s3(nextday_forecast, bucket_name, key, stripped_dt)
