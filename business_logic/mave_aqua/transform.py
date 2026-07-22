import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_harvest_data(df):
    """
    Applies cleaning logic to remove rows with blanks in critical columns.
    """
    logger.info("Starting cleaning process for Harvest Data...")
    clean_df = df.copy()

    clean_df = clean_df.replace(r"^\s*$", np.nan, regex=True)

    critical_columns = ["batch_type", "current_growth_stage", "final_yield_kg"]

    columns_to_check = [
        col for col in critical_columns if col in clean_df.columns
        ]

    clean_df = clean_df.dropna(subset=columns_to_check, how="any")

    logger.info(f"Harvest Data cleaned. {len(clean_df)} rows remaining.")
    return clean_df


def clean_lagoon_data(df):
    """
    Applies cleaning and transformation logic to the lagoon environmental log.
    """
    logger.info("Starting cleaning process for Lagoon Data...")

    clean_df = df.copy()

    clean_df = clean_df.dropna(subset=["station_id"])

    if "seeding_date" in clean_df.columns:
        clean_df["seeding_date"] = pd.to_datetime(clean_df["seeding_date"])

    logger.info(f"Lagoon Data cleaned. {len(clean_df)} rows remaining.")
    return clean_df
