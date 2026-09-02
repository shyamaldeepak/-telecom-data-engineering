"""Apache Airflow DAG for Telecom 360° End-to-End Lakehouse Pipeline.

Orchestrates:
1. Batch & Streaming Ingestion into Bronze Layer
2. Data Quality & Cleansing into Silver Layer (with SCD Type 2)
3. Gold Lakehouse Analytical Aggregations (Customer 360, Network Health, Outages, Revenue)
4. Churn Feature Extraction & XGBoost Batch Scoring
"""

import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "telecom_data_engineering",
    "depends_on_past": False,
    "start_date": datetime.datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

with DAG(
    dag_id="telecom_360_lakehouse_pipeline",
    default_args=default_args,
    description="End-to-End Telecom 360 Lakehouse Ingestion, Quality, Marts, and ML Scoring",
    schedule_interval="0 * * * *",  # Hourly batch run
    catchup=False,
    tags=["telecom", "lakehouse", "medallion", "ml"],
) as dag:

    # 1. Raw Generation / Ingestion into Bronze
    ingest_bronze = BashOperator(
        task_id="ingest_to_bronze",
        bash_command="python pyspark/transformations/raw_ingestion.py",
    )

    # 2. Bronze to Silver Transformation & Quality Quarantine
    transform_silver = BashOperator(
        task_id="transform_to_silver",
        bash_command="python pyspark/transformations/bronze_to_silver.py",
    )

    # 3. Silver to Gold Aggregations & Marts
    transform_gold = BashOperator(
        task_id="transform_to_gold",
        bash_command="python pyspark/transformations/silver_to_gold.py",
    )

    # 4. Churn Model Training & Evaluation
    train_model = BashOperator(
        task_id="train_churn_model",
        bash_command="python ml/train.py",
    )

    # 5. Batch Churn Scoring & Watchlist Generation
    score_churn = BashOperator(
        task_id="score_customer_churn",
        bash_command="python ml/inference.py",
    )

    # Task Pipeline Dependencies
    ingest_bronze >> transform_silver >> transform_gold >> train_model >> score_churn
