import base64
import json
from typing import Dict

import boto3
from logger import log


def retrieve_ssm_parameter_value() -> Dict | str:
    """
    Retrieve Google service account credentials from
    AWS Systems Manager Parameter Store.

    Returns:
        Dict | str: Parsed credentials dict, or raw string if not JSON

    Raises:
        ValueError: If the parameter value cannot be parsed
    """
    client = boto3.session.Session().client(service_name="ssm")
    response = client.get_parameter(
        Name="/production/google-service-account/credentials",
        WithDecryption=True
    )
    value = response["Parameter"]["Value"]

    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError) as e:
        log.info(f"Could not parse SSM parameter as JSON. ERROR {str(e)}")
        pass

    try:
        decoded = base64.b64decode(value).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        log.info(
            f"Could not parse SSM parameter as base64-encoded JSON. "
            f"ERROR {str(e)}"
        )
        pass

    return value


def hive_partitioned_bucket_setup(prefix: str, date_str: str) -> str:
    """
    Generates a Hive-style partitioned S3 key from a date string.

    Args:
        prefix (str): The top-level prefix e.g. 'raw' or 'transformed'.
        date_str (str): A date string in 'YYYY-MM-DD' format.

    Returns:
        str: A partitioned S3 key e.g. 'raw/year=2026/month=04/day=25'.
    """

    parts = date_str.split("-")
    year, month, day = parts
    key = f"{prefix}/year={year}/month={month}/day={day}"
    log.info(f"Generated S3 key: {key}")
    return key
