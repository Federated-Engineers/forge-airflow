
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

logger = logging.getLogger(__name__)


def get_current_datetime():
    """
    Return the current UTC date and time.
    """
    logger.info("Getting current UTC datetime.")

    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H:%M:%S")


def get_yesterday():
    """
    Return yesterday's date in UTC.
    """
    return (
        datetime.now(timezone.utc).date() - timedelta(days=1)
    ).strftime("%Y-%m-%d")


def get_partitioned_date(target_date: str, df: pd.DataFrame):
    """
    Add year, month and day partition columns.
    """
    dt = datetime.strptime(target_date, "%Y-%m-%d")

    df["year"] = dt.year
    df["month"] = dt.month
    df["day"] = dt.day

    return df


def date_partition_path(current_datetime: str):
    """
    Return a Hive-style partition path.
    """
    year, month, day = current_datetime.split("_")[0].split("-")

    return f"year={year}/month={month}/day={day}"