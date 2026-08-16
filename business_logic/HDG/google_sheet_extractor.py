import logging

from plugins.gspread_auth import get_google_sheets_data

logger = logging.getLogger(__name__)


def extract_google_sheet(sheet_id: str):
    """Extractdata from Googlesheets and return it as a DataFrame."""
    df = get_google_sheets_data(gsheet_id=sheet_id, sheet_name="Sheet1")
    return df
