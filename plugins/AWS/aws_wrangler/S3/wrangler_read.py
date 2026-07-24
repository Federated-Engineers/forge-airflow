"""S3 reader helpers built on awswrangler.

Usage:
- Pass an S3 path string or a list of S3 paths.
- Pass any awswrangler reader options through params.

Examples:
- read_csv_data("s3://my-bucket/raw/data.csv")
- read_parquet_data(
            "s3://my-bucket/curated/orders/",
            dataset=True,
            columns=["order_id", "created_at"],
    )

Notes:
- This module sets wr.engine to python to avoid Ray runtime usage.
- CSV reads default to UTF-8 but can still be overridden via params.
"""

import awswrangler as wr
import pandas as pd

wr.engine.set("python")


def read_csv_data(s3_path: str | list[str], **params) -> pd.DataFrame:
    """Read CSV data from S3 into a DataFrame."""
    return wr.s3.read_csv(path=s3_path, encoding="utf-8", **params)


def read_json_data(s3_path: str | list[str], **params) -> pd.DataFrame:
    """Read JSON data from S3 into a DataFrame."""
    return wr.s3.read_json(path=s3_path, **params)


def read_parquet_data(s3_path: str | list[str], **params) -> pd.DataFrame:
    """Read Parquet data from S3 into a DataFrame."""
    return wr.s3.read_parquet(path=s3_path, **params)


def read_excel_data(s3_path: str | list[str], **params) -> pd.DataFrame:
    """Read Excel data from S3 into a DataFrame."""
    return wr.s3.read_excel(path=s3_path, **params)
