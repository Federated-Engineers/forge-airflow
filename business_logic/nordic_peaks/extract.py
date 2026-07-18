import json
from typing import Any

import gspread
from google.oauth2 import service_account

GSHEETS_READONLY_SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def parse_service_account_json(service_account_json: str) -> dict[str, Any]:
    """Parse a Google service account JSON string into a dictionary."""
    try:
        payload = json.loads(service_account_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid JSON in GSHEETS_SERVICE_ACCOUNT_JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "GSHEETS_SERVICE_ACCOUNT_JSON must decode to a JSON object"
        )

    return payload


def fetch_worksheet_records(
    spreadsheet_id: str,
    worksheet_name: str,
    service_account_info: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return worksheet rows as dictionaries keyed by the header row."""
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=GSHEETS_READONLY_SCOPE,
    )
    client = gspread.authorize(credentials)
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    return worksheet.get_all_records(default_blank="")
