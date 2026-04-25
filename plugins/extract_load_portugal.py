import awswrangler as wr
import logging
from plugins.google_sheets import authenticate_google_sheet

log = logging.getLogger(__name__)


def extract_portugal(file_key):
    """Extracts Data from s3 dump and filters for portugal data only
    Returns:
    Portugal Data
    """
    log.info(f"Reading {file_key} from S3")

    df = wr.s3.read_parquet(f"s3://{bucket}/{file_key}")
    filtered_df = df[df["plant_country"].str.strip().str.upper() == 'PORTUGAL']
    if filtered_df.empty:
        log.warning("No Portugal records found.")

    return filtered_df


def write_df_to_sheet(df, spreadsheet_id, sheetname):
    """
    Authenticate with Google Sheets API and
    writes data from a Dataframe to Google Sheet.
    If the Sheet is empty, adds a header to the first row,
    else it appends data from the Dataframe to the Sheets. 
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    google_cred = authenticate_google_sheet(scopes)
    worksheet = google_cred.open_by_key(spreadsheet_id).worksheet(sheetname)
    first_row = worksheet.row_values(1)
    if not first_row:
        log.info("Sheet is empty, writing headers and data...")
        worksheet.append_rows([df.columns.tolist()] + df.values.tolist())
    else:
        log.info("Sheet has data, appending rows only...")
        worksheet.append_rows(df.values.tolist())
