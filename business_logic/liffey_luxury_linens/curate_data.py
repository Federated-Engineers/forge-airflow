
import datetime

import pandas as pd

from business_logic.liffey_luxury_linens.transform import \
    deduplicate_crm_first_touch
from plugins.AWS.aws_wrangler.S3.wrangler_read import read_csv_data
from plugins.AWS.aws_wrangler.S3.wrangler_write import write_parquet_data


def write_to_curated_zone(
    loaded_data: dict[str, str],
    bucket: str,
    run_datetime: datetime.datetime,
) -> None:
    run_date = run_datetime.strftime("%Y-%m-%d")

    for source, landing_zone_path in loaded_data.items():
        df = get_raw_data(landing_zone_path)

        if source == "crm_data":
            df = deduplicate_crm_first_touch(df)

        df["run_date"] = run_date

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
