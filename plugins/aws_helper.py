import boto3


def get_s3_client():
    """
    Create an Amazon S3 client.
    """
    return boto3.client("s3")


def get_ssm_parameter(parameter_name: str) -> str:
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.
    """
    client = boto3.client(
        "ssm",
        region_name="eu-central-1",
    )

    response = client.get_parameter(
        Name=parameter_name,
        WithDecryption=True,
    )

    return response["Parameter"]["Value"]