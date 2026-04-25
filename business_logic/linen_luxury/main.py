import os
from io import BytesIO

import boto3
import gspread
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from extraction import extraction
from load import move_file_s3
from transform import transformation

load_dotenv()
db_name=os.getenv("DATABASE")
db_username=os.getenv("DB_USERNAME")
db_pass=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")


access_key_id=os.getenv("AWS_ACCESS_KEY_ID")
secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
s3_bucket_name=os.getenv("S3_BUCKET_NAME")
influencer_key=os.getenv("KEY1")
order_key=os.getenv("KEY2")
athena_db_name=os.getenv("ATHENA_DB")



sheet_name=os.getenv("SHEET_NAME")
tab_name=os.getenv("WORKSHEET_NAME")



def run_etl_to_s3():
    google_data, postgres_data=extraction()

    influencer_data, orders_data=transformation(google_data,postgres_data)

    move_file_s3(influencer_data, influencer_key)
    move_file_s3(orders_data, order_key)


if __name__ == "__main__":
    run_etl_to_s3()