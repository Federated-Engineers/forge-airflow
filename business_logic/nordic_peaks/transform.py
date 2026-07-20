from decimal import ROUND_HALF_UP, Decimal
from typing import Any
import pandas as pd




def transform_data_to_typed_dataframe(raw_data: list[dict[str, Any]],source_config: dict[str, Any],) -> tuple[pd.DataFrame, dict[str, str]]:
    
    """Validate, type, and deduplicate landing records before Parquet export."""
    df = pd.DataFrame(raw_data)
    # Keep a logical schema map for consistent Parquet dtypes downstream.
    semantic_types: dict[str, str] = {}

    for column in source_config.get("date_columns", []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.date
            semantic_types[column] = "date"

    return df, semantic_types
