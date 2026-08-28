import json
import logging
from pathlib import Path

import pandas as pd

from business_logic.bbss.config import (BUCKET_NAME, RAW_PREFIX,
                                        TRANSFORMED_PREFIX)
from plugins.date_utils import (date_partition_path, get_current_datetime,
                                get_partitioned_date)
from plugins.pandas_helper import add_ingestion_timestamp
from plugins.s3_helper import read_json, write_dataframe_to_s3_glue

logger = logging.getLogger(__name__)


def flatten_weather_data(
    weather: dict,
    location_name: str,
) -> list[dict]:
    """
    Flatten a WeatherAPI response into hourly records.
    """
    location = weather["location"]
    forecast = weather["forecast"]["forecastday"][0]

    rows = []

    for hour in forecast["hour"]:
        rows.append(
            {
                "location_name": location_name,
                "latitude": location["lat"],
                "longitude": location["lon"],
                "forecast_date": forecast["date"],
                "forecast_time": hour["time"],
                "temperature_c": hour["temp_c"],
                "condition": hour["condition"]["text"],
                "wind_kph": hour["wind_kph"],
                "gust_kph": hour["gust_kph"],
                "pressure_mb": hour["pressure_mb"],
                "humidity": hour["humidity"],
                "cloud": hour["cloud"],
                "precipitation_mm": hour["precip_mm"],
                "visibility_km": hour["vis_km"],
                "chance_of_rain": hour["chance_of_rain"],
            }
        )

    return rows


def transform_weather_data():
    """
    Transform raw weather data into a partitioned dataset.
    """
    config_path = Path(__file__).parent / "weather_config.json"

    with open(config_path, "r", encoding="utf-8") as file:
        weather_config = json.load(file)

    locations = weather_config["locations"]

    current_datetime = get_current_datetime()
    partition_path = date_partition_path(current_datetime)

    target_date = current_datetime.split("_")[0]

    records = []

    for location in locations:
        object_key = (
            f"{RAW_PREFIX}/"
            f"{location['name']}/"
            f"{partition_path}/"
            "weather.json"
        )

        weather = read_json(
            bucket_name=BUCKET_NAME,
            object_key=object_key,
        )

        records.extend(
            flatten_weather_data(
                weather=weather,
                location_name=location["name"],
            )
        )

    df = pd.DataFrame(records)

    df = df.drop_duplicates(
        subset=["location_name", "forecast_time"]
    )

    df = add_ingestion_timestamp(df)

    df = get_partitioned_date(
        target_date,
        df,
    )

    write_dataframe_to_s3_glue(
        df=df,
        path=f"s3://{BUCKET_NAME}/{TRANSFORMED_PREFIX}",
        filename_prefix="weather_",
        partition_cols=["year", "month", "day"],
        mode="overwrite_partitions",
    )

    logger.info("Weather transformation completed.")

    return df
