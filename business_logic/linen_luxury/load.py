import awswrangler as wr
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.athena import AthenaHook


def anthena_creation(df, tablename, s3_path):
    """
    Register the Parquet file as an external table in AWS Athena.
    """
    athena_hook = AthenaHook()

    athena_db_name = Variable.get("Anthena_DB")
    athena_output = Variable.get("Anthena_Output_S3")

    type_map = {
        'int64': 'BIGINT',
        'int32': 'INT',
        'float64': 'DOUBLE',
        'datetime64[ns]': 'TIMESTAMP',
        'datetime64[us]': 'TIMESTAMP',
        'bool': 'BOOLEAN',
        'object': 'STRING'
    }

    col_definitions = [
        f"`{col}` {type_map.get(str(dtype).lower(), 'STRING')}"
        for col, dtype in df.dtypes.items()
    ]
    columns = ", ".join(col_definitions)

    create_table = (
        f"CREATE EXTERNAL TABLE IF NOT EXISTS {athena_db_name}.{tablename} "
        f"({columns}) STORED AS PARQUET LOCATION '{s3_path}' "
        "TBLPROPERTIES ('parquet.compress'='SNAPPY');"
    )
    athena_hook.run_query(
        query=create_table,
        query_context={'Database': athena_db_name},
        result_configuration={'OutputLocation': athena_output}
    )


def move_file_s3(df, key, tablename):
    """
    Upload DataFrame to S3 as Parquet and trigger Athena registration.
    """
    s3_bucket_name = Variable.get("S3_BUCKET_NAME")
    s3_path = f"s3://{s3_bucket_name}/{key}"

    wr.s3.to_parquet(
        df=df,
        path=s3_path,
        index=False,
        compression="snappy"
    )

    # Use rsplit to get the directory path for Athena
    anthena_creation(df, tablename, s3_path.rsplit('/', 1)[0] + "/")
