import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from .evaluate import evaluate_classification, evaluate_ranking
from sklearn.model_selection import train_test_split


class RuleBasedBaseline:
    """
    Transparent, rule-based baseline model for lead conversion prediction.
    Applies heuristic domain weights on engagement, intent, recency, and account signals.
    """

    def __init__(self, base_prob: float = 0.15):
        self.base_prob = base_prob

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculate conversion probabilities using transparent heuristic rules.
        Returns a 1D array of predicted probabilities between 0.0 and 1.0.
        """
        prob = np.full(len(X), self.base_prob, dtype=float)

        # 1. Intent signals (highest weight)
        if "demo_requested" in X.columns:
            prob += X["demo_requested"].values * 0.25
        if "pricing_page_visit" in X.columns:
            prob += X["pricing_page_visit"].values * 0.10

        # 2. Engagement signals
        if "email_clicked" in X.columns:
            prob += np.minimum(X["email_clicked"].values, 5) * 0.03
        if "call_made" in X.columns:
            prob += np.minimum(X["call_made"].values, 5) * 0.02
        if "web_visit" in X.columns:
            prob += np.minimum(X["web_visit"].values, 10) * 0.01

        # 3. Recency penalty (less recent contact reduces probability)
        if "days_since_last_contact" in X.columns:
            days = X["days_since_last_contact"].values
            recency_penalty = np.where(days > 90, 0.10, np.where(days > 30, 0.05, 0.0))
            prob -= recency_penalty

        # 4. History and stage signals
        if "previous_purchase" in X.columns:
            prob += X["previous_purchase"].values * 0.05
        if "opportunity_stage_Qualified" in X.columns:
            prob += X["opportunity_stage_Qualified"].values * 0.05
        if "opportunity_stage_Proposal" in X.columns:
            prob += X["opportunity_stage_Proposal"].values * 0.08

        return np.clip(prob, 0.01, 0.99)

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary conversion label based on threshold.
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculate 0-100 integer lead scores.
        """
        proba = self.predict_proba(X)
        return np.round(proba * 100).astype(int)


def split_data(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Splits model-ready dataset into train and test sets with fixed random seed.
    Separates lead_id, features, and target.
    """
    if "lead_id" not in df.columns or "converted" not in df.columns:
        raise ValueError("Dataset must contain 'lead_id' and 'converted' columns.")

    lead_ids = df["lead_id"]
    y = df["converted"]
    X = df.drop(columns=["lead_id", "converted"])

    (
        X_train,
        X_test,
        y_train,
        y_test,
        ids_train,
        ids_test,
    ) = train_test_split(
        X, y, lead_ids, test_size=test_size, random_state=random_state, stratify=y
    )

    return X_train, X_test, y_train, y_test, ids_train, ids_test




def run_baseline_pipeline(
    data_path: str = "data/model_ready_features.csv",
    output_dir: str = "data",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Executes the full baseline model pipeline: loads data, splits train/test,
    predicts using RuleBasedBaseline, computes classification and ranking metrics,
    and saves results to baseline_metrics.json.
    """
    df = pd.read_csv(data_path)
    X_train, X_test, y_train, y_test, ids_train, ids_test = split_data(
        df, test_size=test_size, random_state=random_state
    )

    baseline = RuleBasedBaseline()

    # Predict on test set
    y_test_proba = baseline.predict_proba(X_test)
    y_test_pred = baseline.predict(X_test, threshold=0.5)

    y_test_arr = y_test.values

    classification_metrics = evaluate_classification(
        y_test_arr, y_test_pred, y_test_proba
    )
    ranking_metrics = evaluate_ranking(y_test_arr, y_test_proba)

    results = {
        "model_type": "RuleBasedBaseline",
        "dataset_path": str(data_path),
        "total_records": len(df),
        "train_records": len(X_train),
        "test_records": len(X_test),
        "test_size": test_size,
        "random_state": random_state,
        "classification_metrics": classification_metrics,
        "ranking_metrics": ranking_metrics,
    }

    # Save metrics artifact
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    with open(out_path / "baseline_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    results = run_baseline_pipeline(
        "f:/pending project/CRM project/backend/data/model_ready_features.csv",
        "f:/pending project/CRM project/backend/data",
    )
    print("Baseline pipeline executed successfully:")
    print(json.dumps(results, indent=2))
