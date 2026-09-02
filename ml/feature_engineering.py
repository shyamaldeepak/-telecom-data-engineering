"""Feature Engineering for Telecom Churn Prediction.

Loads features from Gold layer, encodes categorical variables,
and produces standardized train/test datasets.
"""

import os
from typing import Tuple, List
import pandas as pd
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "tenure_days",
    "monthly_price",
    "total_data_gb",
    "total_calls",
    "dropped_calls",
    "dropped_call_ratio",
    "failed_payments",
    "is_female",
    "contract_month_to_month",
    "contract_one_year",
]


def prepare_features(
    gold_features_path: str = "data/gold/churn_features.parquet",
    test_size: float = 0.25,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
    if not os.path.exists(gold_features_path):
        raise FileNotFoundError(f"Feature dataset not found at {gold_features_path}")

    df = pd.read_parquet(gold_features_path)

    # Engineered indicators
    df["is_female"] = (df["gender"] == "F").astype(int)
    df["contract_month_to_month"] = (df["contract_type"] == "MONTH_TO_MONTH").astype(int)
    df["contract_one_year"] = (df["contract_type"] == "ONE_YEAR").astype(int)

    X = df[FEATURE_COLUMNS].copy()
    y = df["churn_label"].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if y.nunique() > 1 else None
    )

    return X_train, X_test, y_train, y_test, FEATURE_COLUMNS
