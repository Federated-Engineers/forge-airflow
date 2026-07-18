import boto3

def get_s3_client():
    """
    Create, initializes and return an Amazon S3 client using boto3.
    """
    return boto3.client("s3")


def get_ssm_parameter(ssm_parameter_name: str):
    """Fetch the value of a parameter from AWS Systems Manager Parameter Store
    Args:
        ssm_parameter_name (str): The name of the parameter to fetch.
    Returns:
        str: The value of the specified parameter.
    """
    client = boto3.client('ssm', region_name='eu-central-1',)
    response = client.get_parameter(Name=ssm_parameter_name,
                                    WithDecryption=True)
    ssm_params_value = response['Parameter']['Value']
    return ssm_params_value

