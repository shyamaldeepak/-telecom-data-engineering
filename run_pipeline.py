"""Telecom 360° - Master Pipeline Orchestrator.

Executes the end-to-end data platform:
1. Synthetic Data Generation (Customers, Subscriptions, CDRs, Telemetry, Invoices, Usage)
2. Bronze Layer Raw Ingestion & Partitioning
3. Silver Layer Cleansing, Quarantine Routing & SCD Type 2 History
4. Gold Layer Marts: Customer 360, Network Health, Incident Alarms, Revenue
5. XGBoost Machine Learning Model Training & Batch Churn Scoring
"""

import argparse
import os
import sys
import time

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from data_generator.generate_all import generate_all
from pyspark.transformations.raw_ingestion import run_bronze_ingestion
from pyspark.transformations.bronze_to_silver import run_bronze_to_silver
from pyspark.transformations.silver_to_gold import run_silver_to_gold
from ml.train import train_churn_model
from ml.inference import run_churn_inference


def run_full_pipeline(scale: float = 0.5, skip_generation: bool = False):
    start_time = time.time()
    print("=" * 70)
    print("      TELECOM 360 - END-TO-END DATA ENGINEERING PLATFORM       ")
    print("=" * 70)
    print(f"Execution started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Scale Factor: {scale}")
    print("-" * 70)

    # Step 1: Synthetic Data Generation
    if not skip_generation:
        print("\n>>> [STEP 1/5] Generating Synthetic Telecom Datasets...")
        t0 = time.time()
        generate_all(data_dir=os.path.join(BASE_DIR, "data", "raw"), scale_factor=scale)
        print(f">>> [STEP 1/5] Completed in {time.time() - t0:.2f}s")
    else:
        print("\n>>> [STEP 1/5] Skipping data generation as requested.")

    # Step 2: Bronze Layer Ingestion
    print("\n>>> [STEP 2/5] Ingesting Raw Data into Bronze Lakehouse Layer...")
    t0 = time.time()
    run_bronze_ingestion(
        raw_dir=os.path.join(BASE_DIR, "data", "raw"),
        bronze_dir=os.path.join(BASE_DIR, "data", "bronze")
    )
    print(f">>> [STEP 2/5] Completed in {time.time() - t0:.2f}s")

    # Step 3: Silver Layer Processing (Quality, Quarantine, Deduplication, SCD Type 2)
    print("\n>>> [STEP 3/5] Transforming Bronze to Silver (Quality Checks & SCD2)...")
    t0 = time.time()
    run_bronze_to_silver(
        bronze_dir=os.path.join(BASE_DIR, "data", "bronze"),
        silver_dir=os.path.join(BASE_DIR, "data", "silver"),
        quarantine_dir=os.path.join(BASE_DIR, "data", "quarantine")
    )
    print(f">>> [STEP 3/5] Completed in {time.time() - t0:.2f}s")

    # Step 4: Gold Layer Marts Aggregation
    print("\n>>> [STEP 4/5] Building Gold Marts (Customer 360, Network Health, Outages, Revenue)...")
    t0 = time.time()
    run_silver_to_gold(
        silver_dir=os.path.join(BASE_DIR, "data", "silver"),
        gold_dir=os.path.join(BASE_DIR, "data", "gold")
    )
    print(f">>> [STEP 4/5] Completed in {time.time() - t0:.2f}s")

    # Step 5: Machine Learning (Train Churn Model & Batch Inference)
    print("\n>>> [STEP 5/5] Training XGBoost Churn Model & Running Batch Inference...")
    t0 = time.time()
    train_churn_model(
        gold_features_path=os.path.join(BASE_DIR, "data", "gold", "churn_features.parquet"),
        model_output_dir=os.path.join(BASE_DIR, "ml", "models")
    )
    run_churn_inference(
        gold_dir=os.path.join(BASE_DIR, "data", "gold"),
        model_path=os.path.join(BASE_DIR, "ml", "models", "churn_xgb_model.joblib"),
        output_path=os.path.join(BASE_DIR, "data", "gold", "customer_churn_predictions.parquet")
    )
    print(f">>> [STEP 5/5] Completed in {time.time() - t0:.2f}s")

    total_duration = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Pipeline executed successfully in {total_duration:.2f}s!")
    print("=" * 70)
    print("Outputs available at:")
    print(f"  - Bronze:     {os.path.join(BASE_DIR, 'data', 'bronze')}")
    print(f"  - Silver:     {os.path.join(BASE_DIR, 'data', 'silver')}")
    print(f"  - Gold:       {os.path.join(BASE_DIR, 'data', 'gold')}")
    print(f"  - Quarantine: {os.path.join(BASE_DIR, 'data', 'quarantine')}")
    print(f"  - ML Models:  {os.path.join(BASE_DIR, 'ml', 'models')}")
    print("\nTo launch the interactive visual dashboard, run:")
    print("  streamlit run dashboards/app.py")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telecom 360 Master Pipeline Runner")
    parser.add_argument("--scale", type=float, default=0.5, help="Dataset scale factor (default: 0.5)")
    parser.add_argument("--skip-gen", action="store_true", help="Skip synthetic data generation")
    args = parser.parse_args()

    run_full_pipeline(scale=args.scale, skip_generation=args.skip_gen)
