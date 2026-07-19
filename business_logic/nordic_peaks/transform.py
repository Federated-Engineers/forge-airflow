from decimal import ROUND_HALF_UP, Decimal
from typing import Any
import pandas as pd


def validate_required_columns(
    records: list[dict[str, Any]],
    required_columns: list[str],
    source: str,
) -> None:
    """Fail when a required configured column is missing from snapshot headers."""
    if not records:
        return

    headers = set(records[0].keys())
    missing = [column for column in required_columns if column not in headers]
    if missing:
        raise ValueError(
            f"Source '{source}' is missing required columns: {', '.join(missing)}"
        )


def records_to_typed_dataframe(
    records: list[dict[str, Any]],
    source_config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Validate, type, and deduplicate landing records before Parquet export."""
    df = pd.DataFrame(records)
    # Keep a logical schema map for consistent Parquet dtypes downstream.
    semantic_types: dict[str, str] = {}

    required_columns = source_config.get("required_columns", [])
    if required_columns:
        validate_required_columns(
            records=records,
            required_columns=required_columns,
            source=source_config["source"],
        )

    for column in source_config.get("date_columns", []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.date
            semantic_types[column] = "date"

    for column in source_config.get("integer_columns", []):
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce").astype("Int64")
            semantic_types[column] = "bigint"

    for column in source_config.get("decimal_columns", []):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").apply(
                lambda value: (
                    None
                    if pd.isna(value)
                    else Decimal(str(value)).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )
                )
            )
            semantic_types[column] = "decimal(18,2)"

    dedupe_keys = source_config.get("dedupe_keys", [])
    existing_keys = [key for key in dedupe_keys if key in df.columns]
    if existing_keys:
        # Keep the latest row for duplicate business keys.
        df = df.drop_duplicates(subset=existing_keys, keep="last")

    return df, semantic_types
