"""S3 writer helpers built on awswrangler.

Usage:
- Pass a pandas DataFrame and a bucket name.
- Optionally pass key to override the default object name.
- Pass any awswrangler writer options through params.

Examples:
- write_parquet_data(df, "my-bucket", key="curated/data.parquet")
- write_parquet_data(
            df,
            "my-bucket",
            key="curated/orders",
            dataset=True,
            partition_cols=["country", "year"],
            mode="overwrite_partitions",
    )

Notes:
- This module sets wr.engine to python to avoid Ray runtime usage.
- Each function applies format-specific defaults, which can be
    overridden by params.
"""

import logging

import awswrangler as wr
import pandas as pd

logger = logging.getLogger(__name__)
wr.engine.set("python")


def write_csv_data(df: pd.DataFrame, bucket: str, **params) -> None:
    """Write CSV data to S3."""
    key = params.pop("key", "data.csv")
    path = f"s3://{bucket}/{key}"
    defaults = {"index": False, "encoding": "utf-8"}
    defaults.update(params)
    wr.s3.to_csv(df=df, path=path, **defaults)


def write_parquet_data(df: pd.DataFrame, bucket: str, **params) -> None:
    """Write Parquet data to S3."""
    key = params.pop("key", "data.parquet")
    path = f"s3://{bucket}/{key}"
    defaults = {"index": False}
    defaults.update(params)
    wr.s3.to_parquet(df=df, path=path, **defaults)


def write_json_data(df: pd.DataFrame, bucket: str, **params) -> None:
    """Write JSON data to S3."""
    key = params.pop("key", "data.json")
    path = f"s3://{bucket}/{key}"
    defaults = {"orient": "records", "lines": True, }
    defaults.update(params)
    wr.s3.to_json(df=df, path=path, **defaults)


def write_excel_data(df: pd.DataFrame, bucket: str, **params) -> None:
    """Write Excel data to S3."""
    key = params.pop("key", "data.xlsx")
    path = f"s3://{bucket}/{key}"
    defaults = {"index": False}
    defaults.update(params)
    wr.s3.to_excel(df=df, path=path, **defaults)
