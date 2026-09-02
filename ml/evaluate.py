"""Model Evaluation and Feature Importance Reporter for Telecom Churn.

Evaluates saved XGBoost model, computes feature importance,
and displays decision drivers for customer retention teams.
"""

import json
import os
import sys
import pandas as pd
import xgboost as xgb

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.feature_engineering import prepare_features


def evaluate_model(
    gold_features_path: str = "data/gold/churn_features.parquet",
    model_path: str = "ml/models/churn_xgb_model.joblib",
    metrics_path: str = "ml/models/metrics.json"
):
    print("=" * 60)
    print("Evaluating Telecom Churn Model & Feature Importance")
    print("=" * 60)

    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}. Please train the model first.")
        return

    import joblib
    model = joblib.load(model_path)

    X_train, X_test, y_train, y_test, feature_names = prepare_features(gold_features_path)

    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
        print("Performance Summary:")
        for k, v in metrics.items():
            if k != "features":
                print(f"  {k:15s}: {v}")
        print("-" * 60)

    # Feature Importance
    importances = model.feature_importances_
    fi_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)

    print("Top Churn Predictors (Feature Importance):")
    for _, row in fi_df.iterrows():
        bar = "#" * int(row["importance"] * 40)
        print(f"  {row['feature']:25s}: {row['importance']:.4f} {bar}")

    print("=" * 60)
    return fi_df


if __name__ == "__main__":
    evaluate_model()
