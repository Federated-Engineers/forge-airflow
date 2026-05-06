from business_logic.linen_luxury.extraction import (google_sheet_extraction,
                                                    write_postgres_dataframe)
from business_logic.linen_luxury.load_data_s3 import \
    move_file_and_register_athena


def run_all_scripts():
    postgres_data = write_postgres_dataframe()
    google_sheet_data = google_sheet_extraction()
    move_file_and_register_athena(
        google_sheet_data,
        "lll/influencers_data/influencer_data.parquet",
        "influencer_transactions",
    )
    move_file_and_register_athena(
        postgres_data,
        "lll/influencers_data/orders_data.parquet",
        "order_transactions"
    )
