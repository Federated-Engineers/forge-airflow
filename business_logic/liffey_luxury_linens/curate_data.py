
import pandas as pd
import datetime
from plugins.AWS.aws_wrangler.S3.wrangler_write import write_parquet_data

from plugins.AWS.aws_wrangler.S3.wrangler_read import read_csv_data


def write_to_curated_zone(loaded_data: dict[str, str], bucket: str, run_datetime: datetime.datetime) -> None:

    run_date = run_datetime.strftime("%Y-%m-%d")

    for source, landing_zone_path in loaded_data.items():
        df = get_raw_data(landing_zone_path)
        df["run_date"] = run_date
        year = run_datetime.strftime("%Y")
        month = run_datetime.strftime("%m")
        day = run_datetime.strftime("%d")

        write_parquet_data(
            df=df,
            bucket=bucket,
            dataset=True,
            database="liffey_luxury_linens_db",
            table=source,
            prefix=f"curated_data/{source}",
            mode="overwrite_partitions",
            partition_cols=["run_date"],
        )


def get_raw_data(path: str) -> pd.DataFrame:
    """Read CSV data from S3."""
    return read_csv_data(path)
