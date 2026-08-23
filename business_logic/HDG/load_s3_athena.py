import awswrangler as wr
from airflow.sdk import Variable

"""
function to load data to S3 and register it in Athena.
"""


def load_raw_data_to_s3(df, key):
    """
    Uploads DF to S3 and register Athena_db  using awswrangler.
    """
    config = Variable.get("hdg_json", deserialize_json=True)
    s3_bucket = config.get("s3_bucket_name")

    s3_path = f"s3://{s3_bucket}/raw_files/{key}"

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        index=False,
    )

    print(f"Dataset uploaded to S3 at {s3_path}")

    return s3_path


"""parquet file to the cleaned folder and register it in Athena"""


def move_parquet_to_cleaned_folder(
        df, path_file, tablename, partition_cols=None
        ):

    config = Variable.get(
        "hdg_json",
        deserialize_json=True,
    )

    athena_db = config["athena_db"]

    wr.s3.to_parquet(
        df=df,
        path=path_file,
        dataset=True,
        database=athena_db,
        table=tablename,
        mode="append",
        index=False,
        compression="snappy",
        partition_cols=partition_cols,
    )

    print(
        f"Moved to {path_file} and in Athena table {tablename}"
        )
