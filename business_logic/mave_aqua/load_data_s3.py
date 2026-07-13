import awswrangler as wr
from airflow.models import Variable


def save_raw_to_s3(df, filename):
    """
    Saves the unmodified raw DataFrame as a single flat Parquet file 
    in the 'raw_files' folder.
    """
    s3_bucket = Variable.get("S3_BUCKET_NAME")
    
    
    raw_path = f"s3://{s3_bucket}/raw_files/{filename}"
    print(f"Uploading raw file to: {raw_path}")
    
    
    wr.s3.to_parquet(
        df=df,
        path=raw_path,
        dataset=False,
        compression="snappy"
    )
    print(f"Raw Parquet file successfully saved: {filename}")



def move_file_and_register_athena(df, key, tablename, partition_cols=None):
    """
    Uploads DF to S3 and register Athena_db  using awswrangler.
    """

    s3_bucket = Variable.get("S3_BUCKET_NAME")
    athena_db = Variable.get("Anthena_DB")

    s3_path = f"s3://{s3_bucket}/{key}"

    # 1. Automatically create the Glue/Athena database if it doesn't exist
    if athena_db not in wr.catalog.databases().values:
        print(f"Creating Glue/Athena database: {athena_db}")
        wr.catalog.create_database(name=athena_db)

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        dataset=True,
        database=athena_db,
        table=tablename,
        mode="overwrite",
        index=False,
        compression="snappy",
        partition_cols=partition_cols
    )

    print(f"Dataset uploaded and registered in {athena_db}.{tablename}")
