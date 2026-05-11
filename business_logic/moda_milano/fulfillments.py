import json
from datetime import datetime, timezone

import pandas as pd
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from plugins.aws import copy_data_from_s3, write_to_s3_for_glue
from plugins.logger import log


def process_fulfillment_data():
    hook = S3Hook()
    config = Variable.get("moda_milano_config", deserialize_json=True)

    source_bucket = config["FULFILLMENT_BUCKET"]
    source_prefix = config["FULFILLMENTS_PREFIX"]
    dest_bucket = config["MODA_MILANO_BUCKET"]
    glue_database = config["GLUE_DB_NAME"]

    last_run = Variable.get("fulfillments_last_run", default_var=None)
    last_run_date = (
        datetime.fromisoformat(last_run)) if last_run \
        else datetime.min.replace(tzinfo=timezone.utc
                                  )

    run_start = str(datetime.now(tz=timezone.utc))
    # run_start here is created early in the function call so if
    # new objects are added during the lifetime of this function,
    # they're not missed in the next run

    client = hook.get_conn()
    paginator = client.get_paginator("list_objects_v2")
    new_keys = []

    for page in paginator.paginate(Bucket=source_bucket, Prefix=source_prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] >= last_run_date:
                new_keys.append(obj["Key"])

    if not new_keys:
        log.info("No new fulfillment data found")
        return

    all_dfs = []
    for key in new_keys:
        data = copy_data_from_s3(source_bucket, key)
        parsed = json.loads(data)
        parsed_data = parsed if isinstance(parsed, list) else [parsed]
        all_dfs.append(pd.DataFrame(parsed_data))

    df = pd.concat(all_dfs, ignore_index=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["fulfillment_year"] = df["timestamp"].dt.year.astype(str)
    df["fulfillment_month"] = df["timestamp"].dt.month.astype(str).str.zfill(2)
    df["fulfillment_day"] = df["timestamp"].dt.day.astype(str).str.zfill(2)

    write_to_s3_for_glue(
            df,
            dest_bucket,
            "fulfillments",
            glue_database,
            "fulfillments",
            ["fulfillment_year", "fulfillment_month", "fulfillment_day"]
    )
    log.info(f"Wrote {len(df)} fulfillment records with partitions")
    Variable.set("fulfillments_last_run", run_start)
