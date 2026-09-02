"""Batch Inference Engine for Customer Churn Scoring.

Scores active subscribers using the trained XGBoost model and produces
a prioritized retention watchlist in the Gold layer.
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.feature_engineering import FEATURE_COLUMNS


def run_churn_inference(
    gold_dir: str = "data/gold",
    model_path: str = "ml/models/churn_xgb_model.joblib",
    output_path: str = "data/gold/customer_churn_predictions.parquet"
) -> pd.DataFrame:
    print("=" * 60)
    print("Starting Batch Churn Inference Pipeline")
    print("=" * 60)

    features_path = os.path.join(gold_dir, "churn_features.parquet")
    c360_path = os.path.join(gold_dir, "customer_360.parquet")

    if not os.path.exists(features_path) or not os.path.exists(model_path):
        raise FileNotFoundError(f"Missing required files: {features_path} or {model_path}")

    df_features = pd.read_parquet(features_path)
    df_c360 = pd.read_parquet(c360_path) if os.path.exists(c360_path) else pd.DataFrame()

    df_features["is_female"] = (df_features["gender"] == "F").astype(int)
    df_features["contract_month_to_month"] = (df_features["contract_type"] == "MONTH_TO_MONTH").astype(int)
    df_features["contract_one_year"] = (df_features["contract_type"] == "ONE_YEAR").astype(int)

    X = df_features[FEATURE_COLUMNS].copy()

    import joblib
    model = joblib.load(model_path)

    probabilities = model.predict_proba(X)[:, 1]
    predictions = (probabilities >= 0.50).astype(int)

    results = df_features[["customer_id", "contract_type", "monthly_price", "total_data_gb", "dropped_call_ratio", "failed_payments"]].copy()
    results["churn_probability"] = probabilities.round(4)
    results["predicted_churn"] = predictions

    # Segment into Risk Categories
    results["risk_tier"] = pd.cut(
        results["churn_probability"],
        bins=[-0.01, 0.25, 0.60, 1.0],
        labels=["LOW", "MEDIUM", "HIGH"]
    )

    if not df_c360.empty and "first_name" in df_c360.columns:
        results = results.merge(
            df_c360[["customer_id", "first_name", "last_name", "city", "plan_name", "customer_status"]],
            on="customer_id",
            how="left"
        )

    # Sort high risk customers first
    results = results.sort_values(by="churn_probability", ascending=False).reset_index(drop=True)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    results.to_parquet(output_path, index=False, engine="pyarrow")

    high_risk_count = (results["risk_tier"] == "HIGH").sum()
    print(f"[Inference] Scored {len(results)} customers.")
    print(f"[Inference] High Risk Watchlist: {high_risk_count} customers flagged.")
    print(f"[SUCCESS] Scored predictions saved to: {output_path}")
    print("=" * 60)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch churn scoring")
    parser.add_argument("--gold-dir", type=str, default="data/gold", help="Gold data dir")
    parser.add_argument("--model", type=str, default="ml/models/churn_xgb_model.joblib", help="Model path")
    parser.add_argument("--output", type=str, default="data/gold/customer_churn_predictions.parquet", help="Output path")
    args = parser.parse_args()

    run_churn_inference(gold_dir=args.gold_dir, model_path=args.model, output_path=args.output)
