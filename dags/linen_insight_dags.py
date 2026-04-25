from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from pendulum import datetime

from business_logic.linen_luxury.extraction import extraction
from business_logic.linen_luxury.load import move_file_s3
from business_logic.linen_luxury.transform import transformation

with DAG(
    dag_id="Liffey_Linens_Insights",
    start_date=datetime(2026, 4, 22),
    schedule="0 */1 * * *",
    catchup=False  
    ) as dag:

    def run_all_scripts():
        google_data, postgres_data = extraction()


        influencer_data, orders_data = transformation(google_data, postgres_data)


        move_file_s3(
            influencer_data, 
            "lll/influencers_data/influencer_data.parquet", 
            "influencer_transactions"
        )
        
        move_file_s3(
            orders_data, 
            "lll/orders_data/orders_data.parquet", 
            "order_transactions"
        )

    run_etl_script_to_s3 = PythonOperator(
        task_id="run_all_scripts",
        python_callable=run_all_scripts,
    )

    run_etl_script_to_s3