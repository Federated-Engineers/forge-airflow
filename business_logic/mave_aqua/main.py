from business_logic.mave_aqua.extraction import write_postgres_dataframe
from business_logic.mave_aqua.load_data_s3 import save_raw_to_s3, move_file_and_register_athena
from business_logic.mave_aqua.transform import clean_lagoon_data, clean_harvest_data

def run_all_scripts():
    raw_lagoon_data, raw_harvest_data = write_postgres_dataframe()


    save_raw_to_s3(raw_lagoon_data, "lagoon_environmental_log_raw.parquet")
    save_raw_to_s3(raw_harvest_data, "harvest_lifecycle_record_raw.parquet")


    cleaned_lagoon = clean_lagoon_data(raw_lagoon_data)
    cleaned_harvest = clean_harvest_data(raw_harvest_data)

    move_file_and_register_athena(
        df=cleaned_lagoon,
        key="cleaned_and_partitioned/lagoon_environmental_log/",
        tablename="lagoon_environmental_log",
        partition_cols=["station_id"]
    )

    move_file_and_register_athena(
        df=cleaned_harvest,
        key="cleaned_and_partitioned/harvest_lifecycle_record/",
        tablename="harvest_lifecycle_record",
        partition_cols=["batch_type"]
    )