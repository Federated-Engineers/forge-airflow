import awswrangler as wr
import pandas as pd

wr.engine.set("python")


def read_raw_data_from_s3(s3_uri: str) -> pd.DataFrame:
    """Load a landing snapshot JSON from S3."""
    df = wr.s3.read_csv(path=s3_uri, encoding="utf-8")
    return df
