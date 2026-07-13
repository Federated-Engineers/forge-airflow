from typing import List

from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from logger import log


def list_keys(hook: S3Hook, bucket_name: str, prefix: str) -> List | None:
    """List all S3 object keys under a given bucket and prefix.
        Args:
            hook: An initialized S3Hook.
            bucket_name: Name of the S3 bucket to search.
            prefix: Key folder path to filter objects under.

        Returns:
            A list of matching S3 object keys, or None if no keys are found.
        """
    keys = hook.list_keys(bucket_name=bucket_name, prefix=prefix)
    keys = [k for k in keys if not k.endswith("/")]
    log.info(f"Found {len(keys)} files to process")

    return keys
