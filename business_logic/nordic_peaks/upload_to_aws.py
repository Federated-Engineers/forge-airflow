from typing import Any

from business_logic.nordic_peaks.extract_to_s3 import (
    read_snapshot_from_s3, write_snapshot_to_s3_if_missing)
from business_logic.nordic_peaks.load_processed import write_processed_parquet
from business_logic.nordic_peaks.s3_keys import build_landing_key
from business_logic.nordic_peaks.s3_keys import \
    build_processed_key as _build_processed_key


def build_processed_key(source: str, run_dt: Any) -> str:
    """Compatibility wrapper for callers using the former signature."""
    del source, run_dt
    return _build_processed_key()


__all__ = [
    "build_landing_key",
    "build_processed_key",
    "read_snapshot_from_s3",
    "write_processed_parquet",
    "write_snapshot_to_s3_if_missing",
]
