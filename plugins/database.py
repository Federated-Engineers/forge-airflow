from airflow.providers.postgres.hooks.postgres import PostgresHook


def get_postgres_data(conn_id, query):
    """
    module to fetch data from a Postgres database.
    Can be used by any DAG in the system.
    """
    pg_hook = PostgresHook(postgres_conn_id=conn_id)

    df = pg_hook.get_pandas_df(sql=query)

    return df
