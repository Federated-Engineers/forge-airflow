import logging

import awswrangler as wr
import pandas as pd

from business_logic.scardinavas.config import (bucket_name, date_columns,
                                               glue_database)
from plugins.s3_helper import write_dataframe_to_s3_glue

logger = logging.getLogger(__name__)
wr.engine.set("python")


def process_to_partitioned_s3(dataset_name, logical_date):
    """
    Read a dataset's raw CSV from S3, derive year/month/day partition
    columns from its date column, and write it out as partitioned
    Parquet registered in the Glue catalog.
    """
    extraction_date = logical_date.strftime("%Y-%m-%d")

    raw_path = (
        f"s3://{bucket_name}/raw/{dataset_name}/"
        f"{dataset_name}_{extraction_date}.csv"
    )
    processed_path = f"s3://{bucket_name}/processed/{dataset_name}/"

    df = wr.s3.read_csv(path=raw_path, encoding="utf-8")

    date_col = date_columns[dataset_name]
    df[date_col] = pd.to_datetime(df[date_col])

    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.month
    df["day"] = df[date_col].dt.day

    write_dataframe_to_s3_glue(
        df=df,
        path=processed_path,
        filename_prefix=dataset_name,
        partition_cols=["year", "month", "day"],
        database=glue_database,
        table=dataset_name,
        mode="overwrite_partitions",
    )

    logger.info("%s processed successfully", dataset_name)
