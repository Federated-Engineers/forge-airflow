from business_logic.linen_luxury.extraction import (google_sheet_extraction,
                                                    postgress_extraction)
from business_logic.linen_luxury.load import move_file_s3


def run_all_scripts():
    postgres_data = postgress_extraction()
    google_sheet_data = google_sheet_extraction()
    move_file_s3(
        google_sheet_data,
        "lll/influencers_data/influencer_data.parquet",
        "influencer_transactions",
    )
    move_file_s3(
        postgres_data, "lll/influencers_data/orders_data.parquet",
        "order_transactions"
    )
