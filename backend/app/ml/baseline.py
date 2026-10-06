import json
import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .evaluate import evaluate_classification, evaluate_ranking


class RuleBasedBaseline:
    """
    Transparent, rule-based baseline model for lead conversion prediction.
    Applies heuristic domain weights on engagement, intent, recency, and account signals.
    """

    def __init__(self, base_prob: float = 0.15):
        self.base_prob = base_prob
        self.feature_contract_version = "v2_phase2"
        self.weights = {
            "intent": {
                "demo_requested": 0.25,
                "pricing_page_visit": 0.10,
            },
            "engagement": {
                "email_clicked_max5": 0.03,
                "call_made_max5": 0.02,
                "web_visit_max10": 0.01,
            },
            "recency": {
                "days_since_last_contact_gt30": -0.05,
                "days_since_last_contact_gt90": -0.10,
            },
            "opportunity": {
                "previous_purchase": 0.05,
                "opportunity_stage_Qualified": 0.05,
                "opportunity_stage_Proposal": 0.08,
            },
            "financial": {
                "deal_value_gt_100k": 0.10,
                "deal_value_gt_10k": 0.05,
                "annual_revenue_gt_1m": 0.05,
            }
        }

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculate conversion probabilities using transparent heuristic rules.
        Returns a 1D array of predicted probabilities between 0.0 and 1.0.
        """
        prob = np.full(len(X), self.base_prob, dtype=float)

        # 1. Intent signals (highest weight)
        if "demo_requested" in X.columns:
            prob += X["demo_requested"].values * self.weights["intent"]["demo_requested"]
        if "pricing_page_visit" in X.columns:
            prob += X["pricing_page_visit"].values * self.weights["intent"]["pricing_page_visit"]

        # 2. Engagement signals
        if "email_clicked" in X.columns:
            prob += np.minimum(X["email_clicked"].values, 5) * self.weights["engagement"]["email_clicked_max5"]
        if "call_made" in X.columns:
            prob += np.minimum(X["call_made"].values, 5) * self.weights["engagement"]["call_made_max5"]
        if "web_visit" in X.columns:
            prob += np.minimum(X["web_visit"].values, 10) * self.weights["engagement"]["web_visit_max10"]

        # 3. Recency penalty (less recent contact reduces probability)
        if "days_since_last_contact" in X.columns:
            days = X["days_since_last_contact"].values
            recency_penalty = np.where(
                days > 90, 
                abs(self.weights["recency"]["days_since_last_contact_gt90"]), 
                np.where(days > 30, abs(self.weights["recency"]["days_since_last_contact_gt30"]), 0.0)
            )
            prob -= recency_penalty

        # 4. History and stage signals
        if "previous_purchase" in X.columns:
            prob += X["previous_purchase"].values * self.weights["opportunity"]["previous_purchase"]
        if "opportunity_stage_Qualified" in X.columns:
            prob += X["opportunity_stage_Qualified"].values * self.weights["opportunity"]["opportunity_stage_Qualified"]
        if "opportunity_stage_Proposal" in X.columns:
            prob += X["opportunity_stage_Proposal"].values * self.weights["opportunity"]["opportunity_stage_Proposal"]

        # 5. Financial signals (Bucketed to prevent unbounded domination)
        if "deal_value" in X.columns:
            deal_val = X["deal_value"].values
            prob += np.where(deal_val > 100000, self.weights["financial"]["deal_value_gt_100k"], 
                             np.where(deal_val > 10000, self.weights["financial"]["deal_value_gt_10k"], 0.0))
            
        if "annual_revenue" in X.columns:
            rev = X["annual_revenue"].values
            prob += np.where(rev > 1000000, self.weights["financial"]["annual_revenue_gt_1m"], 0.0)

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
        Maps directly from conversion probability to align with Phase 1 bands.
        """
        proba = self.predict_proba(X)
        return np.round(proba * 100).astype(int)
        
    def rank_leads(self, X: pd.DataFrame, ids: pd.Series) -> pd.DataFrame:
        """
        Deterministically rank leads.
        Sort by:
        1. Score (Descending)
        2. deal_value (Descending, if available)
        3. lead_id (Ascending)
        """
        scores = self.score(X)
        
        df_rank = pd.DataFrame({
            'lead_id': ids,
            'score': scores
        })
        
        # Ensure lead_id is string for deterministic sorting
        df_rank['lead_id'] = df_rank['lead_id'].astype(str)
        
        if "deal_value" in X.columns:
            df_rank['deal_value'] = X['deal_value'].values
            df_rank = df_rank.sort_values(
                by=['score', 'deal_value', 'lead_id'], 
                ascending=[False, False, True]
            )
        else:
            df_rank = df_rank.sort_values(
                by=['score', 'lead_id'], 
                ascending=[False, True]
            )
            
        return df_rank.reset_index(drop=True)


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

    # Output detailed baseline artifact
    results = {
        "model_type": "RuleBasedBaseline",
        "baseline_version": "1.0.0",
        "feature_contract_version": baseline.feature_contract_version,
        "creation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "weights": baseline.weights,
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
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_file = base_dir / "data" / "model_ready_features.csv"
    out_folder = base_dir / "data"
    results = run_baseline_pipeline(
        str(data_file),
        str(out_folder),
    )
    print("Baseline pipeline executed successfully:")
    print(json.dumps(results, indent=2))
