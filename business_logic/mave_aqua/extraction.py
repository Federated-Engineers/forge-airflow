import logging

from plugins.database import get_postgres_data

logger = logging.getLogger(__name__)


def write_postgres_dataframe():
    """
    Extracts data from Postgres database using internal modules.
    """
    query1 = "SELECT * FROM historical.lagoon_environmental_log"
    query2 = "SELECT * FROM historical.harvest_lifecycle_record"

    logger.info("Starting Postgress Extraction from supabase")
    lagoon_tbl_data = get_postgres_data(
        conn_id="supabase_postgres",
        query=query1
    )
    harvest_tbl_data = get_postgres_data(
        conn_id="supabase_postgres",
        query=query2
    )
    logger.info(f"Successfully extracted {len(lagoon_tbl_data)} rows from db")
    logger.info(f"Successfully extracted {len(harvest_tbl_data)} rows from db")

    return lagoon_tbl_data, harvest_tbl_data
