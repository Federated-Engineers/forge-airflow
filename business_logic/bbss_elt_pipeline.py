import requests
from datetime import datetime
import numpy as np
import json
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.models import Variable

API_KEY = Variable.get("WEATHER_API_KEY")
BASE_URL = "https://api.weatherapi.com/v1"
logger = logging.getLogger(__name__)
s3_hook = S3Hook()

class WeatherAPIError(Exception):
    """Raised when WeatherAPI returns an error response."""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"WeatherAPI error {code}: {message}")


def get_forecast() -> dict:
    logger.info("Fetching forecast from WeatherAPI for Calvia...")
    params = {
        "key": API_KEY,
        "q": 'Calvia',
        "days": 2,
        "aqi": "yes",
        "alerts": "yes"
    }

    response = requests.get(f"{BASE_URL}/forecast.json", params=params)

    if not response.ok:
        error = response.json()["error"]
        logger.error(f"WeatherAPI error {error['code']}: {error['message']}")
        raise WeatherAPIError(error["code"], error["message"])

    forecast = response.json()
    tomorrow_hours = forecast['forecast']['forecastday'][1]['hour']
    logger.info(f"Successfully fetched {len(tomorrow_hours)} hourly records")
    return tomorrow_hours

def generate_s3_partitioned_key(prefix: str, date_str: str) -> str:
    parts = date_str.split("-")
    year, month, day = parts
    key = f"{prefix}/year={year}/month={month}/day={day}"
    logger.info(f"Generated S3 key: {key}")
    return key


def dump_json_to_s3(nextday_forecast: list, bucket_name: str, partition_key: str):
    logger.info(f"Dumping raw JSON to s3://{bucket_name}/{partition_key}")
    try:
        s3_hook.load_string(
            string_data=json.dumps(nextday_forecast),
            key=f"{partition_key}/bbss_forecast.json",
            bucket_name=bucket_name,
            replace=True,
        )
        logger.info("Raw JSON successfully uploaded to S3")
    except Exception as e:
        logger.error(f"Failed to upload raw JSON to S3: {e}")
        raise

def transform_forecast(nextday_forecast: list) -> list:
    logger.info(f"Transforming {len(nextday_forecast)} hourly records...")
    flat_data = []
    for hour in nextday_forecast:
        flat = {k: v for k, v in hour.items() if k not in ['condition', 'wind_dir', 'time_epoch']}
        flat['time'] = hour['time'].split(' ')[1]
        flat['wind_degree_sin'] = np.sin(np.radians(hour['wind_degree']))
        flat['wind_degree_cos'] = np.cos(np.radians(hour['wind_degree']))
        flat_data.append(flat)
    logger.info(f"Transformation complete — {len(flat_data)} records ready")
    return flat_data

def send_parquet_to_s3(transformed: list, bucket_name: str,  partition_key: str):
    logger.info(f"Converting {len(transformed)} records to Parquet and uploading to s3://{bucket_name}/{partition_key}")
    try:
        weather_df = pd.DataFrame(transformed)
        buffer = io.BytesIO()
        pq.write_table(pa.Table.from_pandas(weather_df), buffer)
        buffer.seek(0)

        s3_hook.load_bytes(
            bytes_data=buffer.read(),
            key=f"{partition_key}/bbss_forecast.parquet",
            bucket_name=bucket_name,
            replace=True,
        )
        logger.info("Parquet file successfully uploaded to S3")
    except Exception as e:
        logger.error(f"Failed to upload Parquet to S3: {e}")
        raise
