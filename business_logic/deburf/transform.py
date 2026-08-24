import boto3

from plugins.s3_helper import (read_latest_data_from_s3,
                               write_dataframe_to_s3_glue)

from .config import bucket_name, paths

dms_client = boto3.client("dms")


def get_replication_task_arn(dms_client, task_id: str) -> str:
    """
    Resolve a DMS replication task ARN from its human-readable
    replication-task-id (e.g. the name set in Terraform).
    """
    response = dms_client.describe_replication_tasks(
        Filters=[{"Name": "replication-task-id", "Values": [task_id]}]
    )
    tasks = response.get("ReplicationTasks", [])
    if not tasks:
        raise ValueError(f"No replication task found with id: {task_id}")
    return tasks[0]["ReplicationTaskArn"]


def start_dms_replication_task(dms_client, task_id: str) -> dict:
    replication_task_arn = get_replication_task_arn(dms_client, task_id)

    describe_response = dms_client.describe_replication_tasks(
        Filters=[
            {
                "Name": "replication-task-arn",
                "Values": [replication_task_arn]
                }
            ]
    )
    task_status = describe_response["ReplicationTasks"][0]["Status"]
    start_type = (
        "start-replication" if task_status == "ready" else "reload-target"
    )

    response = dms_client.start_replication_task(
        ReplicationTaskArn=replication_task_arn,
        StartReplicationTaskType=start_type,
    )
    return response["ReplicationTask"]


def write_data_glue():

    dataframes = {table_name: read_latest_data_from_s3(bucket_name, path)
                  for table_name, path in paths.items()}

    routes_df = dataframes["routes"]
    shipments_df = dataframes["shipments"]

    # route table
    write_dataframe_to_s3_glue(
        df=routes_df,
        path=f"s3://{bucket_name}/processed/logistics_routes_partitioned",
        filename_prefix="logistics_routes",
        partition_cols=["transport_mode"],
        database="deburf_db",
        table="logistics_routes",
        mode="overwrite_partitions",
    )

    # shipments table
    write_dataframe_to_s3_glue(
        df=shipments_df,
        path=f"s3://{bucket_name}/processed/logistics_shipments_partitioned",
        filename_prefix="logistics_shipments",
        partition_cols=["transport_mode", "cargo_type"],
        database="deburf_db",
        table="logistics_shipments",
        mode="overwrite_partitions",
    )
