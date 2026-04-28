import json
import logging

import awswrangler as wr
import numpy as np
import pandas as pd
import requests
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sdk import Variable

config = Variable.get("bbss_weather_api_config", deserialize_json=True)
logger = logging.getLogger(__name__)
s3_hook = S3Hook()


def get_forecast() -> dict:
    """
    Fetches the next day's hourly forecast for the selected location.

    Raises an Exception if the API returns a non-200 status code.

    Returns:
        list: A list of hourly forecast records for the next day.
    """

    logger.info("Fetching forecast from WeatherAPI for Calvia...")
    params = {
        "key": config.get("API_KEY"),
        "q": config.get("LOCATION"),
        "days": 2,
        "aqi": "yes",
        "alerts": "yes"
    }
    base_url = config.get("BASE_URL")
    response = requests.get(f"{base_url}/forecast.json", params=params)

    if response.status_code != 200:
        error = response.json()["error"]
        logger.error(f"WeatherAPI error {error['code']}: {error['message']}")
        raise Exception(f"API error {error['code']}: {error['message']}")

    forecast = response.json()
    tomorrow_hours = forecast['forecast']['forecastday'][1]['hour']
    logger.info(f"Successfully fetched {len(tomorrow_hours)} hourly records")
    return tomorrow_hours


def dump_json_to_s3(nextday_forecast: list, bucket_name: str, s3_key: str):
    """
    Serializes the raw forecast data as JSON and uploads it to S3.

    Args:
        nextday_forecast (list): List of hourly forecast records to upload.
        bucket_name (str): The target S3 bucket name.
        s3_key (str): The S3 key prefix for the partitioned path.

    Raises:
        Exception: If the upload to S3 fails.
    """

    logger.info(f"Sending Raw JSON to s3://{bucket_name}/{s3_key}")
    try:
        s3_hook.load_string(
            string_data=json.dumps(nextday_forecast),
            key=f"{s3_key}/bbss_forecast.json",
            bucket_name=bucket_name,
            replace=True,
        )
        logger.info("Raw JSON successfully uploaded to S3")
    except Exception as e:
        logger.error(f"Failed to upload raw JSON to S3: {e}")
        raise


def transform_forecast(nextday_forecast: list) -> list:
    """
    Transforms raw hourly forecast records into a flattened structure.

    Drops unnecessary fields, extracts the time component, and engineers
    sine and cosine features from wind degree for cyclical encoding.

    Args:
        nextday_forecast (list): List of raw hourly forecast records.

    Returns:
        list: A list of transformed and flattened forecast records.
    """

    logger.info(f"Transforming {len(nextday_forecast)} hourly records...")
    flat_data = []
    for hour in nextday_forecast:
        excluded = {'condition', 'wind_dir', 'time_epoch'}
        flat = {
            k: v for k, v in hour.items()
            if k not in excluded
            }
        flat['time'] = hour['time'].split(' ')[1]
        flat['wind_degree_sin'] = np.sin(np.radians(hour['wind_degree']))
        flat['wind_degree_cos'] = np.cos(np.radians(hour['wind_degree']))
        flat_data.append(flat)
    logger.info(f"Transformation complete — {len(flat_data)} records ready")
    return flat_data


def send_parquet_to_s3(transformed: list, bucket_name: str,  s3_key: str):
    """
    Converts transformed forecast records to Parquet format and uploads to S3.

    Args:
        transformed (list): List of transformed forecast records.
        bucket_name (str): The target S3 bucket name.
        s3_key (str): The S3 key prefix for the partitioned path.

    Raises:
        Exception: If the Parquet conversion or S3 upload fails.
    """

    logger.info(f"Converting {len(transformed)} records to Parquet")
    try:
        weather_df = pd.DataFrame(transformed)

        wr.s3.to_parquet(
            df=weather_df,
            path=f"s3://{bucket_name}/{s3_key}/bbss_forecast.parquet",
        )
        logger.info("Parquet sent to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload Parquet to S3: {e}")
        raise
