"""End-to-End Pipeline Integration Tests."""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.transformations.raw_ingestion import run_bronze_ingestion
from pyspark.transformations.bronze_to_silver import run_bronze_to_silver
from pyspark.transformations.silver_to_gold import run_silver_to_gold
from ml.inference import run_churn_inference


def test_lakehouse_pipeline_artifacts():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_dir = os.path.join(base, "data", "gold")

    c360_path = os.path.join(gold_dir, "customer_360.parquet")
    net_path = os.path.join(gold_dir, "network_health.parquet")
    pred_path = os.path.join(gold_dir, "customer_churn_predictions.parquet")

    assert os.path.exists(c360_path), "customer_360.parquet must exist"
    assert os.path.exists(net_path), "network_health.parquet must exist"
    assert os.path.exists(pred_path), "customer_churn_predictions.parquet must exist"

    df_c360 = pd.read_parquet(c360_path)
    assert len(df_c360) > 0
    assert "total_data_gb" in df_c360.columns
    assert "customer_id" in df_c360.columns

    df_pred = pd.read_parquet(pred_path)
    assert len(df_pred) > 0
    assert "churn_probability" in df_pred.columns
    assert "risk_tier" in df_pred.columns
