from typing import Any


def build_landing_folders(source: str, run_dt: Any) -> str:
    """Create immutable landing key with day partition and run timestamp."""
    year = run_dt.strftime("%Y")
    month = run_dt.strftime("%m")
    day = run_dt.strftime("%d")
    hhmm = run_dt.strftime("%H%M")
    return (
        f"landing_zone/source={source}/year={year}/month={month}/day={day}/"
        f"{source}_{hhmm}Z.csv"
    )
