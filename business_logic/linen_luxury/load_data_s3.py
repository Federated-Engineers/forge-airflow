import awswrangler as wr
from airflow.models import Variable


def move_file_and_register_athena(df, key, tablename):
    """
    Uploads DF to S3 and register Athena_db  using awswrangler.
    """

    config = Variable.get("LINEN_LUXURY_LOAD_CONFIG", deserialize_json=True)

    s3_bucket = config.get("s3_bucket_name")
    athena_db = config.get("athena_db")

    s3_path = f"s3://{s3_bucket}/{key.rsplit('/', 1)[0]}"

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=True,
        database=athena_db,
        table=tablename,
        mode="overwrite",
        index=False,
        compression="snappy",
    )

    print(f"Dataset uploaded and registered in {athena_db}.{tablename}")
