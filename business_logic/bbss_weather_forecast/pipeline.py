import logging

import awswrangler as wr
import numpy as np
import pandas as pd
import requests
from airflow.sdk import Variable

config = Variable.get("bbss_weather_api_config", deserialize_json=True)
logger = logging.getLogger(__name__)


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


def send_parquet_to_s3(
        nextday_forecast: list,
        bucket_name: str, 
        s3_key: str,
        stripped_dt: str
    ):
    """
    Flattens raw hourly forecast records and uploads them as Parquet to S3.

    Args:
        nextday_forecast (list): List of raw forecast records from WeatherAPI.
        bucket_name (str): The target S3 bucket name.
        s3_key (str): The S3 key prefix for the partitioned path.
        stripped_dt (str): Date str with hyphens removed used in the filename.

    Raises:
        Exception: If the Parquet upload to S3 fails.
    """

    logger.info(f"Transforming {len(nextday_forecast)} hourly records...")
    flat_data = []
    for hour in nextday_forecast:
        flat = {k: v for k, v in hour.items()}
        flat['date'] = hour['time'].split(' ')[0]
        flat['time'] = hour['time'].split(' ')[1]
        flat_data.append(flat)
    logger.info(f"Flattening complete — {len(flat_data)} records ready")
    s3_path=f"s3://{bucket_name}/{s3_key}/bbss-weather-{stripped_dt}.parquet"
    logger.info(f"Converting {len(flat_data)} records to Parquet")
    try:
        weather_df = pd.DataFrame(flat_data)
        wr.s3.to_parquet(
            df=weather_df,
            path=s3_path
        )
        logger.info(f"Parquet sent to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload Parquet to S3: {e}")
        raise
