from typing import Tuple

import pandas as pd
from airflow.models import Variable

from plugins.aws import write_to_s3_for_glue
from plugins.database import fetch_incremental_from_table, get_postgres_engine
from plugins.logger import log


def get_moda_milano_config(
        ) -> Tuple[str, str, str, str, str, str, str, str, str]:
    config = Variable.get("moda_milano_config", deserialize_json=True)

    bucket = config["MODA_MILANO_BUCKET"]
    database_name = config["DATABASE_NAME"]
    username = config["DB_USERNAME"]
    password = config["DB_PASSWORD"]
    host = config["DB_HOST"]
    schema = config["DB_SCHEMA"]
    glue_database = config["GLUE_DB_NAME"]
    orders_table = config["ORDERS_TABLE"]
    products_table = config["PRODUCTS_TABLE"]

    return (
        bucket, database_name, username, password, host, schema,
        glue_database, orders_table, products_table
         )


def copy_orders():
    (
        bucket, database_name, username, password, host, schema, glue_database,
        orders_table, _) = get_moda_milano_config()

    engine = get_postgres_engine(database_name, username, password, host)

    checkpoint = Variable.get("last_ordered_at", default_var=None)
    df = fetch_incremental_from_table(
        engine, schema, orders_table, "ordered_at", checkpoint
    )

    if df.empty:
        log.info("No new orders found, skipping copy")
        return

    log.info(f"Found {len(df)} orders from {orders_table}")

    df["ordered_at"] = pd.to_datetime(df["ordered_at"])

    df["order_year"] = df["ordered_at"].dt.year.astype(str)
    df["order_month"] = df["ordered_at"].dt.month.astype(str).str.zfill(2)
    df["order_day"] = df["ordered_at"].dt.day.astype(str).str.zfill(2)

    write_to_s3_for_glue(
        df, bucket, "orders", glue_database, "orders",
        ["order_year", "order_month", "order_day"]
    )
    log.info(f"Copied {len(df)} orders from {orders_table}")

    Variable.set("last_ordered_at", df["ordered_at"].max().isoformat())
    log.info("Last order checkpoint marked")


def copy_products():
    (bucket, database_name, username, password, host, schema,
     glue_database, _, products_table) = get_moda_milano_config()

    engine = get_postgres_engine(database_name, username, password, host)

    checkpoint = Variable.get("last_product_created_at", default_var=None)
    df = fetch_incremental_from_table(
        engine, schema, products_table, "created_at", checkpoint
    )

    if df.empty:
        log.info("No new products found, skipping copy")
        return

    log.info(f"Found {len(df)} products from {products_table}")

    write_to_s3_for_glue(
        df, bucket, "products", glue_database, "products", []
    )

    Variable.set("last_product_created_at", df["created_at"].max())
    log.info("Last product checkpoint marked")
