from airflow.sdk import Variable

from business_logic.bbss_weather_forecast.pipeline import (dump_json_to_s3,
                                                           get_forecast,
                                                           send_parquet_to_s3,
                                                           transform_forecast)
from plugins.aws import hive_partitioned_bucket_setup

bbss_s3_bucket = Variable.get("BUCKET_NAME")


def fetch(**kwargs):
    nextday_forecast = get_forecast()
    kwargs['ti'].xcom_push(key='nextday_forecast', value=nextday_forecast)


def dump_raw_json(**kwargs):
    ti = kwargs['ti']
    nextday_forecast = ti.xcom_pull(key='nextday_forecast', task_ids='_fetch')
    bucket_name = bbss_s3_bucket
    date_str = nextday_forecast[0]['time'].split(' ')[0]
    key = hive_partitioned_bucket_setup("raw", date_str)
    dump_json_to_s3(nextday_forecast, bucket_name, key)


def transform(**kwargs):
    ti = kwargs['ti']
    nextday_forecast = ti.xcom_pull(key='nextday_forecast', task_ids='_fetch')
    transformed = transform_forecast(nextday_forecast)
    ti.xcom_push(key='transformed', value=transformed)


def send_transformed_parquet(**kwargs):
    ti = kwargs['ti']
    transformed = ti.xcom_pull(key='transformed', task_ids='_transform')
    nextday_forecast = ti.xcom_pull(key='nextday_forecast', task_ids='_fetch')
    bucket_name = bbss_s3_bucket
    date_str = nextday_forecast[0]['time'].split(' ')[0]
    key = hive_partitioned_bucket_setup("transformed", date_str)
    send_parquet_to_s3(transformed, bucket_name, key)

