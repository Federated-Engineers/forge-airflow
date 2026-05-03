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
            f"Could not parse SSM as base64-encoded JSON. " f"ERROR {str(e)}"
        )
        pass

    return value
