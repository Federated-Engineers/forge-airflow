import logging

from plugins.date_utils import get_partitioned_date
from plugins.s3_helper import (read_latest_data_from_s3,
                               write_dataframe_to_s3_glue)

from business_logic.bbss.config import (ANALYTICS_PREFIX, BUCKET_NAME,
                                        TRANSFORMED_PREFIX)

logger = logging.getLogger(__name__)


def calculate_risk_score(row):
    """
    Calculate the weather risk score.
    """
    score = 0

    if row["wind_kph"] > 25:
        score += 30

    if row["gust_kph"] > 40:
        score += 30

    if row["precipitation_mm"] > 0:
        score += 20

    if row["visibility_km"] < 5:
        score += 20

    return score


def get_risk_level(score):
    """
    Categorize the weather risk level.
    """
    if score >= 61:
        return "High"

    if score >= 31:
        return "Medium"

    return "Low"


def build_weather_analytics():
    """
    Build the analytics dataset.
    """
    df = read_latest_data_from_s3(
        bucket=BUCKET_NAME,
        prefix=TRANSFORMED_PREFIX,
    )

    df = get_partitioned_date(
        target_date=df["forecast_date"].iloc[0],
        df=df,
    )

    df["risk_score"] = df.apply(
        calculate_risk_score,
        axis=1,
    )

    df["risk_level"] = df["risk_score"].apply(
        get_risk_level,
    )

    write_dataframe_to_s3_glue(
        df=df,
        path=f"s3://{BUCKET_NAME}/{ANALYTICS_PREFIX}",
        filename_prefix="weather_analytics_",
        partition_cols=["year", "month", "day"],
        mode="overwrite_partitions",
    )

    logger.info("Weather analytics completed.")

    return df
