from typing import Any

import awswrangler as wr


def read_raw_data_from_s3(s3_uri: str) -> list[dict[str, Any]]:
    """Load a landing snapshot JSON from S3."""
    records = wr.s3.read_json(path=s3_uri)
    return records
