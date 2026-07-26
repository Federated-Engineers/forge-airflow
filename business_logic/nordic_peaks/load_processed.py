import awswrangler as wr
import pandas as pd

from plugins.AWS.aws_wrangler.S3.wrangler_write import write_parquet_data

wr.engine.set("python")


def load_data(
    dataframe: pd.DataFrame,
    bucket: str,
    semantic_types: dict[str, str],
    source: str,
    partition_date_column: str,
) -> None:
    """Write a dataset partitioned by source and business-date year/month."""
    if partition_date_column not in dataframe.columns:
        raise ValueError(
            f"Partition date column '{partition_date_column}' is missing"
        )

    dataframe = dataframe.copy()
    partition_dates = pd.to_datetime(
        dataframe[partition_date_column], errors="coerce"
    )
    if partition_dates.isna().any():
        raise ValueError(
            "Partition date column "
            f"'{partition_date_column}' contains invalid dates"
        )

    dataframe["source"] = source
    dataframe["year"] = partition_dates.dt.strftime("%Y")
    dataframe["month"] = partition_dates.dt.strftime("%m")

    parquet_dtypes = dict(semantic_types or {})
    parquet_dtypes["source"] = "string"
    parquet_dtypes["year"] = "string"
    parquet_dtypes["month"] = "string"

    write_parquet_data(
        df=dataframe,
        bucket=bucket,
        prefix="processed_zone/",
        dataset=True,
        partition_cols=["source", "year", "month"],
        mode="overwrite_partitions",
        index=False,
        dtype=parquet_dtypes,
    )
