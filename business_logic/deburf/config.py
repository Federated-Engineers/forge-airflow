bucket_name = "federated-production-forge-data-engineers-deburf-data-lake"

glue_db = "deburf_db"

paths = {
    "routes": "raw/public/logistics_routes",
    "shipments": "raw/public/logistics_shipments",
}

replication_task_id = "deburf-dms-replication-task"
