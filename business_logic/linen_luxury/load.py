import os
from io import BytesIO

import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.athena import AthenaHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def anthena_creation(df, tablename, s3_path):
    athena_hook = AthenaHook(aws_conn_id='aws_conn')


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
    columns=", ".join([f"`{col}` {type_map.get(str(dtype).lower(), 'STRING')}" for col, dtype in df.dtypes.items()])

    create_table = f""" 
    CREATE EXTERNAL TABLE IF NOT EXISTS {athena_db_name}.{tablename} ({columns})
    STORED AS PARQUET
    LOCATION '{s3_path}'
    TBLPROPERTIES ('parquet.compress'='SNAPPY');
    """

    athena_hook.run_query(
       query=create_table,
        query_context={'Database': athena_db_name},
        result_configuration={'OutputLocation': athena_output}
    )

    print(f"Anthena Table '{tablename} registration submitted")



def move_file_s3(df,key,tablename):

    s3_hook = S3Hook(aws_conn_id='aws_conn')
    s3_bucket_name = Variable.get("S3_BUCKET_NAME")

    pq_buffer = BytesIO()
    df.to_parquet(pq_buffer, engine='pyarrow', index=False, compression='snappy')
  

    s3_hook.load_file_obj(
        file_obj=pq_buffer,
        key=key,
        bucket_name=s3_bucket_name,
        replace=True
    )
    
    s3_folder_path = f"s3://{s3_bucket_name}/{os.path.dirname(key)}/"

    anthena_creation(df, tablename, s3_folder_path)

    print(f"Full Load Complete: {key}")


