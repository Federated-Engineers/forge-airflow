import pandas as pd
from logger import log
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_postgres_engine(
        db_name: str,
        db_username: str,
        db_password: str,
        db_host: str
        ) -> Engine:
    """
    Create and return a SQLAlchemy engine for a PostgreSQL database.

    Args:
        db_name: Name of the Postgres database.
        db_username: Username
        db_password: Password
        db_host: Hostname

    Returns:
        A SQLAlchemy Engine
    """
    log.info(f"Connecting to {db_name}")
    return create_engine(
        f"postgresql+psycopg2://{db_username}:{db_password}"
        f"@{db_host}/{db_name}"
    )


def fetch_incremental_from_table(
        engine: Engine,
        schema: str,
        table_name: str,
        timestamp_col: str,
        checkpoint: str | None = None
        ) -> pd.DataFrame:
    """
    Fetch rows from a Postgres table incrementally
    if a checkpoint is provided, or in full.

    Args:
        engine: SQLAlchemy Engine connected to the target database.
        schema: Database schema containing the table.
        table_name: Name of the table to query.
        timestamp_col: Column used to filter rows for incremental loads.
        checkpoint: ISO-format timestamp string of the last successful load

    Returns:
        A DataFrame containing the fetched rows.
    """

    if checkpoint:
        log.info(f"Incremental load from {checkpoint}")
        query = (f"SELECT * FROM {schema}.{table_name} "
                 f"WHERE {timestamp_col} > '{checkpoint}'")
    else:
        log.info(f"No checkpoint found for {table_name}, running full load")
        query = f"SELECT * FROM {schema}.{table_name}"

    with engine.connect() as conn:
        return pd.read_sql(sql=query, con=conn.connection)
