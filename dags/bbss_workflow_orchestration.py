from airflow.decorators import dag, task
from airflow.models import Variable
from pendulum import datetime as pendulum_datetime
from datetime import timedelta
from business_logic.bbss_elt_pipeline import (
    get_forecast, generate_s3_partitioned_key,
    dump_json_to_s3, transform_forecast, send_parquet_to_s3
)
from business_logic.slack_utils import slack_failure_alert, slack_success_alert

@dag(
    dag_id="bbss_weather_forecast_ingestion_pipeline",
    schedule="0 23 * * *",
    start_date=pendulum_datetime(2026, 4, 23),
    catchup=False,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(seconds=100),
	"on_failure_callback": slack_failure_alert,
	"on_success_callback": slack_success_alert
    },
    tags=["Federated Engineers","forge","weather", "calvia"],
)
def weather_forecast_pipeline():

    @task()
    def fetch():
        return get_forecast()

    @task()
    def dump_raw(nextday_forecast, bucket_name):
        date_str = nextday_forecast[0]['time'].split(' ')[0]
        key = generate_s3_partitioned_key("raw", date_str)
        dump_json_to_s3(nextday_forecast, bucket_name, key)

    @task()
    def transform(nextday_forecast):
        return transform_forecast(nextday_forecast)

    @task()
    def send_parquet(transformed, nextday_forecast, bucket_name):
        date_str = nextday_forecast[0]['time'].split(' ')[0]
        key = generate_s3_partitioned_key("transformed", date_str)
        send_parquet_to_s3(transformed, bucket_name, key)

    bucket_name = Variable.get("BUCKET_NAME")
    nextday_forecast = fetch()
    dump_raw(nextday_forecast, bucket_name)
    transformed = transform(nextday_forecast)
    send_parquet(transformed, nextday_forecast, bucket_name)

weather_forecast_pipeline()

