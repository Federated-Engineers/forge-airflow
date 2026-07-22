import awswrangler as wr
from airflow.models import Variable


def move_file_and_register_athena(df, key, tablename, partition_cols=None):
    """
    Uploads DF to S3 and register Athena_db  using awswrangler.
    """
    config = Variable.get("var_json", deserialize_json=True)
    s3_bucket = config.get("s3_bucket_name")
    athena_db = config.get("athena_db")

    s3_path = f"s3://{s3_bucket}/{key}"

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=True,
        database=athena_db,
        table=tablename,
        mode="append",
        index=False,
        compression="snappy",
        partition_cols=partition_cols,
    )

    print(f"Dataset uploaded and registered in {athena_db}.{tablename}")
