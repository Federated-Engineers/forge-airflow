import boto3


def param(name, decrypt=False):
    """get parameter values from aws ssm
    Args:
        name: parameter name
        decrypt: assumes false, use decrypt=True for SecureStrings"""
    ssm = boto3.client("ssm", region_name="eu-central-1")
    return ssm.get_parameter(Name=name, 
                             WithDecryption=decrypt)["Parameter"]["Value"]
