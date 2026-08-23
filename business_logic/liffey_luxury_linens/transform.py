import pandas as pd


def deduplicate_crm_first_touch(df: pd.DataFrame) -> pd.DataFrame:
    """Keep each customer's earliest signup record."""
    required_columns = {"customer_id", "signup_date"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CRM data is missing required columns: {missing}")

    transformed_df = df.copy()
    transformed_df["signup_date"] = pd.to_datetime(
        transformed_df["signup_date"],
        errors="coerce",
    )

    return (
        transformed_df.sort_values(
            ["customer_id", "signup_date"],
            kind="stable",
        )
        .drop_duplicates(subset="customer_id", keep="first")
        .reset_index(drop=True)
    )
