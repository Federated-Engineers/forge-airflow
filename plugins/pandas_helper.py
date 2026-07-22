import pandas as pd


def add_ingestion_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an ingestion timestamp column.
    """
    df["ingestion_timestamp"] = pd.Timestamp.now(tz="UTC")

    return df
