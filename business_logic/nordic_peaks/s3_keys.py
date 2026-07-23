from typing import Any


def build_landing_key(source: str, run_dt: Any) -> str:
    """Create immutable landing key with day partition and run timestamp."""
    year = run_dt.strftime("%Y")
    month = run_dt.strftime("%m")
    day = run_dt.strftime("%d")
    hhmm = run_dt.strftime("%H%M")
    return (
        f"landing_zone/source={source}/year={year}/month={month}/day={day}/"
        f"{source}_{hhmm}Z.csv"
    )


def build_processed_key() -> str:
    """Create the shared processed dataset root path."""
    return "processed_zone/"
