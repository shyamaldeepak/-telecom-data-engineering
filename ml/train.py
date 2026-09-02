"""Machine Learning Training Pipeline for Customer Churn Prediction.

Trains an XGBoost classification model using features from the Gold lakehouse layer,
evaluates precision, recall, and ROC-AUC, and serializes the model artifact.
"""

import argparse
import json
import os
import sys
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.feature_engineering import prepare_features


def train_churn_model(
    gold_features_path: str = "data/gold/churn_features.parquet",
    model_output_dir: str = "ml/models",
    n_estimators: int = 100,
    max_depth: int = 4,
    learning_rate: float = 0.08
):
    print("=" * 60)
    print("Starting XGBoost Customer Churn Model Training")
    print("=" * 60)

    os.makedirs(model_output_dir, exist_ok=True)
    X_train, X_test, y_train, y_test, feature_names = prepare_features(gold_features_path)

    print(f"Training samples: {len(X_train)}, Testing samples: {len(X_test)}")
    print(f"Churn rate in training set: {y_train.mean():.2%}")

    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        auc = 0.5

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "features": feature_names,
    }

    print("-" * 60)
    print(f"Model Performance Metrics:")
    print(f"  Accuracy:  {acc:.2%}")
    print(f"  Precision: {prec:.2%}")
    print(f"  Recall:    {rec:.2%}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {auc:.4f}")
    print("-" * 60)

    # Save model and metrics
    import joblib
    model_path = os.path.join(model_output_dir, "churn_xgb_model.joblib")
    joblib.dump(model, model_path)

    metrics_path = os.path.join(model_output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[SUCCESS] Model saved to: {model_path}")
    print(f"[SUCCESS] Metrics saved to: {metrics_path}")
    print("=" * 60)
    return model, metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train customer churn model")
    parser.add_argument("--features", type=str, default="data/gold/churn_features.parquet", help="Features dataset")
    parser.add_argument("--model-dir", type=str, default="ml/models", help="Model artifact directory")
    args = parser.parse_args()

    train_churn_model(gold_features_path=args.features, model_output_dir=args.model_dir)
