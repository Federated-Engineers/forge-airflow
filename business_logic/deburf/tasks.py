import logging

from business_logic.deburf.transform import (dms_client,
                                             start_dms_replication_task,
                                             write_data_glue)

from .config import replication_task_id

logger = logging.getLogger(__name__)


def run_migration():
    # start_dms_replication_task(replication_task_arn=replication_task_arn)
    start_dms_replication_task(dms_client, task_id=replication_task_id)

    logger.info("All data loaded successfully to S3.")


def transform_data():

    write_data_glue()
