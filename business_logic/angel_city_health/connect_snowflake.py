import base64

import snowflake.connector

from plugins.aws import get_ssm_parameter


def get_snowflake_connection():
    ssm_path = "/snowflake/airflow/private-key"
    private_key = get_ssm_parameter(ssm_path)

    clean_b64 = (
        private_key.replace("-----BEGIN PRIVATE KEY-----", "")
        .replace("-----END PRIVATE KEY-----", "")
        .replace("-----BEGIN RSA PRIVATE KEY-----", "")
        .replace("-----END RSA PRIVATE KEY-----", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace('"', "")
        .strip()
    )
   
    private_key_bytes = base64.b64decode(clean_b64)
    conn = snowflake.connector.connect(
        user="AIRFLOW_USER",
        account="FNCWXVE-UU56570",
        private_key=private_key_bytes,
        warehouse="ACHS_DBT_WH",
        database="ACHS_ANALYTICS",
        schema="STAGING",
        role="AIRFLOW_ROLE"
    )
    print("Snowflake connection established successfully.")
    print(conn)
    return conn
