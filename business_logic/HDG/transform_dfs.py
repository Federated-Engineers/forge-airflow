import awswrangler as wr
import pandas as pd


def transform_dfs(lancy_parquet, rhone_parquet):

    # Read raw Parquet files
    lancy_df = wr.s3.read_parquet(path=lancy_parquet)

    rhone_df = wr.s3.read_parquet(path=rhone_parquet)

    # DEBUG
    print("====================================")
    print("LANCY S3 PATH:")
    print(lancy_parquet)

    print("====================================")
    print("RHONE S3 PATH:")
    print(rhone_parquet)

    print("====================================")

    # Lancy transformations
    lancy_df["Ship_Date"] = pd.to_datetime(lancy_df["Ship_Date"],
                                           errors="coerce")

    lancy_df["month"] = lancy_df["Ship_Date"].dt.to_period("M").astype(str)

    lancy_df["Carrier"] = (
        lancy_df["Carrier"].astype("string").str.strip().str.upper()
        )

    lancy_df["Dest_City"] = (
        lancy_df["Dest_City"].astype("string").str.strip().str.capitalize()
    )

    lancy_df["Value_CHF"] = (
        pd.to_numeric(lancy_df["Value_CHF"], errors="coerce").round(2)
        )

    # Rhone transformations
    rhone_df["Finish_Date"] = pd.to_datetime(
        rhone_df["Finish_Date"], dayfirst=True, errors="coerce"
    )

    rhone_df["Finish_Date"] = pd.to_datetime(
        rhone_df["Finish_Date"], dayfirst=True, errors="coerce"
    )

    rhone_df["month"] = rhone_df["Finish_Date"].dt.to_period("M").astype(str)

    rhone_df["Finish_Date"] = rhone_df["Finish_Date"].dt.strftime("%Y-%m-%d")

    return {
        "lancy": lancy_df,
        "rhone": rhone_df,
    }
