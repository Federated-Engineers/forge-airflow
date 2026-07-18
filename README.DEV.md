## GOOGLE SHEETS EXTRACTION DAG

A ready-to-use DAG has been added to extract rows from Google Sheets and persist them as JSON.

- DAG ID: `google-sheets-extract`
- DAG file: `dags/google_sheets_extract.py`
- Business logic: `business_logic/google_sheets_extractor.py`
- Default schedule: hourly (`0 * * * *`)

### Prerequisites

- Create a Google Cloud service account with access to the Google Sheets API.
- Generate a JSON key for that service account.
- Share the target Google Sheet with the service account email (for example, `service-account-name@project-id.iam.gserviceaccount.com`).

### Configure Airflow Variables

Set the following Airflow Variables in the UI (`Admin -> Variables`) or through CLI:

- `GSHEETS_SPREADSHEET_ID` (required): Spreadsheet ID from the Google Sheet URL.
- `GSHEETS_WORKSHEET_NAME` (optional): Worksheet tab name. Default is `Sheet1`.
- `GSHEETS_OUTPUT_DIR` (optional): Output directory inside the container. Default is `/opt/airflow/logs/google_sheets_extracts`.
- `GSHEETS_SERVICE_ACCOUNT_JSON` (required): Full service account JSON as a single JSON string.

Example CLI commands:

```bash
docker compose exec airflow-apiserver airflow variables set GSHEETS_SPREADSHEET_ID "your_spreadsheet_id"
docker compose exec airflow-apiserver airflow variables set GSHEETS_WORKSHEET_NAME "Sheet1"
docker compose exec airflow-apiserver airflow variables set GSHEETS_OUTPUT_DIR "/opt/airflow/logs/google_sheets_extracts"
docker compose exec airflow-apiserver airflow variables set GSHEETS_SERVICE_ACCOUNT_JSON '{"type":"service_account","project_id":"..."}'
```

### Run The DAG

- Start or restart Airflow containers.
- Open Airflow UI at `localhost:8080`.
- Trigger DAG `google-sheets-extract` manually or unpause it for scheduled execution.
- Check task logs for row count and output file path.


## GOOGLE SHEETS TO MEDALLION LAKE (LANDING + PROCESSED)

The DAG in `dags/google_sheets_extract.py` orchestrates this flow:

1. Authenticate to Google Sheets with a read-only service account.
2. Pull a full snapshot from each configured source sheet.
3. Write raw JSON directly to S3 landing (no local file persistence in task pods).
4. Read landing snapshot, validate + type data, and convert to Parquet.
5. Write Parquet to S3 processed with deterministic monthly overwrite.

### S3 Layout

Single bucket with medallion prefixes:

- `s3://<bucket>/landing/source=<source>/year=<YYYY>/month=<MM>/day=<DD>/<source>_<HHMM>Z.json`
- `s3://<bucket>/processed/source=<source>/year=<YYYY>/month=<MM>/<source>.parquet`
- `s3://<bucket>/curated/` (reserved)

### Airflow Variables

- `DATA_LAKE_BUCKET`: lake bucket name (example `nordic-peaks-oslo`).
- `GSHEETS_SERVICE_ACCOUNT_JSON`: full service-account JSON string.
- `GSHEETS_SOURCES`: JSON array of source configs.

Example `GSHEETS_SOURCES` value:

```json
[
  {
    "source": "finance",
    "spreadsheet_id": "1abc...",
    "worksheet_name": "Sheet1",
    "required_columns": ["transaction_date", "amount_nok", "document_id"],
    "date_columns": ["transaction_date"],
    "decimal_columns": ["amount_nok"],
    "integer_columns": ["invoice_number"],
    "dedupe_keys": ["document_id"]
  },
  {
    "source": "supply_chain",
    "spreadsheet_id": "1xyz...",
    "worksheet_name": "Sheet1",
    "required_columns": ["event_date", "sku", "cost_nok"],
    "date_columns": ["event_date"],
    "decimal_columns": ["cost_nok"],
    "dedupe_keys": ["sku", "event_date"]
  }
]
```

### Why This Pattern

- Landing is immutable and replayable: transforms can be rerun from raw snapshots without re-calling Google API.
- Processed uses deterministic monthly file paths for idempotent retries.
- Hive-style `key=value` partition folders support Athena partition pruning.
- Monthly compaction in processed avoids small-file sprawl at low/medium data volumes.
