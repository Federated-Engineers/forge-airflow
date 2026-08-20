from plugins.AWS.aws_wrangler.S3.wrangler_write import write_csv_data


def load_raw_to_s3(pipeline_metadata, gsheets_data, supabase_data) -> dict[str, str]:
    google_sheets_path = load_google_sheets_data_to_s3(
        pipeline_metadata, gsheets_data)
    supabase_path = load_supabase_data_to_s3(pipeline_metadata, supabase_data)
    return {
        "crm_data": google_sheets_path,
        "transaction_data": supabase_path,
    }


def load_google_sheets_data_to_s3(pipeline_metadata, gsheets_data) -> str:
    bucket_name = pipeline_metadata["bucket_name"]
    run_datetime = pipeline_metadata["run_datetime"]
    google_sheets_metadata = pipeline_metadata["google_sheets_metadata"]
    sheet_name = google_sheets_metadata["sheet_name"].lower().replace(" ", "_")

    landing_key = (
        f"landing_zone/{sheet_name}/{run_datetime.strftime('%Y/%m/%d')}"
        "/raw_data.csv"
    )
    landing_zone_path = f"s3://{bucket_name}/{landing_key}"

    write_csv_data(df=gsheets_data, bucket=bucket_name, prefix=landing_key)

    print(
        f"Google Sheets data successfully loaded to S3 at: {landing_zone_path}")
    return landing_zone_path


def load_supabase_data_to_s3(pipeline_metadata, supabase_data) -> str:
    bucket_name = pipeline_metadata["bucket_name"]
    run_datetime = pipeline_metadata["run_datetime"]

    landing_key = (
        f"landing_zone/transaction_data/{run_datetime.strftime('%Y/%m/%d')}"
        "/supabase_data.csv"
    )
    landing_zone_path = f"s3://{bucket_name}/{landing_key}"

    write_csv_data(df=supabase_data, bucket=bucket_name, prefix=landing_key)

    print(f"Supabase data successfully loaded to S3 at: {landing_zone_path}")
    return landing_zone_path
