import logging

import requests

from business_logic.bbss.config import (
    BUCKET_NAME,
    FORECAST_DAYS,
    LOCATIONS,
    RAW_PREFIX,
    SSM_PARAMETER_NAME,
    WEATHER_API_URL,
)
from plugins.aws_helper import get_ssm_parameter
from plugins.date_utils import (
    date_partition_path,
    get_current_datetime,
)
from plugins.s3_helper import write_json

logger = logging.getLogger(__name__)


def extract_weather_data():
    """
    Extract weather data from WeatherAPI and store the raw JSON in S3.
    """
    api_key = get_ssm_parameter(SSM_PARAMETER_NAME)

    current_datetime = get_current_datetime()
    partition_path = date_partition_path(current_datetime)

    for location in LOCATIONS:

        logger.info(
            f"Extracting weather data for {location['name']}"
        )

        response = requests.get(
            WEATHER_API_URL,
            params={
                "key": api_key,
                "q": location["query"],
                "days": FORECAST_DAYS,
            },
            timeout=30,
        )

        response.raise_for_status()

        object_key = (
            f"{RAW_PREFIX}/"
            f"{location['name']}/"
            f"{partition_path}/"
            "weather.json"
        )

        write_json(
            data=response.json(),
            bucket_name=BUCKET_NAME,
            object_key=object_key,
        )

    logger.info("Weather extraction completed successfully.")