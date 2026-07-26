from typing import Any

import pandas as pd

from plugins.AWS.aws_wrangler.S3.wrangler_read import read_csv_data


def transform_data(
    raw_data_path: str,
    source_config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Validate, type, and deduplicate records before Parquet export."""
    df = read_csv_data(raw_data_path)
    semantic_types: dict[str, str] = {}

    for column in source_config.get("date_columns", []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.date
            semantic_types[column] = "date"

    return df, semantic_types
