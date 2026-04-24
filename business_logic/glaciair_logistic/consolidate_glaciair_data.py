import os
from datetime import date

import awswrangler as wr
import pandas as pd
from airflow.models import Variable

from plugins.google_sheets import (authenticate_google_sheet,
                                   get_google_sheet_records)
from plugins.logger import log

glaciair_variables = Variable.get("GLACIAIR_LOGISTICS", deserialize_json=True)


def load_gsheet_to_s3(file_format: str = "parquet"):
    """
    Load a Google Sheet worksheet into an S3 object.
    - Authenticate google sheet credentials
    - Get google sheet records for all spreadsheet
    - Load them into S3 bucket in as a parquet file

    Arg:
        file_format (str): file format to write the data in s3
        Format can take parquet(default) or csv
    """
    # get airflow variables
    spreadsheet_ids = glaciair_variables.get("spreadsheet_ids")
    spreadsheet_names = glaciair_variables.get("spreadsheet_names")
    worksheet_name = glaciair_variables.get("worksheet_name")
    s3_bucket = glaciair_variables.get("bucket_name")
    s3_prefix = glaciair_variables.get("s3_prefix")

    # create partition date
    partition_date = date.today().strftime("%Y-%m-%d")

    # authenticate google service account
    gc = authenticate_google_sheet(glaciair_variables["scopes"])

    log.info("Google cloud authentication successful!!")

    # loop through each spreasheet to get their data
    for id, gsheet_name in zip(spreadsheet_ids, spreadsheet_names):

        log.info(f"Processing sheet {gsheet_name}... ")

        data = get_google_sheet_records(gc, id, worksheet_name)
        sheet_df = pd.DataFrame(data)

        log.info(f"{gsheet_name} data extracted from google sheet")

        s3_path = os.path.join(
            "s3://",
            s3_bucket,
            s3_prefix,
            partition_date,
            f"{gsheet_name.lower().replace(' ', '_')}.{file_format}",
        )

        if file_format == "parquet":
            wr.s3.to_parquet(df=sheet_df, path=s3_path, index=False)
        elif file_format == "csv":
            wr.s3.to_csv(df=sheet_df, path=s3_path, index=False)
        else:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                "Supported formats are: csv, parquet"
            )

        log.info(
            f"Data {gsheet_name} written to s3 path {s3_path}!!"
            )
