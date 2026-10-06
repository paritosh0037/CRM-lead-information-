import pandas as pd
import numpy as np
import json
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, brier_score_loss
from sklearn.model_selection import train_test_split

from app.ml.baseline import RuleBasedBaseline
from app.ml.model import MLModel
from app.ml.train import evaluate_models

def calculate_metrics(y_true, y_prob):
    y_pred = (y_prob >= 0.5).astype(int)
    roc_auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_prob)
    
    # Precision@K, Recall@K, etc. (simplified Top 10%)
    k = max(1, int(len(y_true) * 0.1))
    top_k_indices = np.argsort(y_prob)[::-1][:k]
    top_k_true = y_true.iloc[top_k_indices] if isinstance(y_true, pd.Series) else y_true[top_k_indices]
    
    precision_at_k = top_k_true.sum() / k
    recall_at_k = top_k_true.sum() / max(1, y_true.sum())
    
    conversion_rate = y_true.mean()
    lift = precision_at_k / conversion_rate if conversion_rate > 0 else 0.0
    
    return {
        "classification": {
            "roc_auc": float(roc_auc),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "brier_score": float(brier)
        },
        "ranking": {
            "precision_at_10_percent": float(precision_at_k),
            "recall_at_10_percent": float(recall_at_k),
            "lift": float(lift),
            "top_10_percent_conversion_rate": float(precision_at_k)
        },
        "calibration": {
            "mean_predicted_probability": float(np.mean(y_prob)),
            "actual_conversion_rate": float(conversion_rate)
        }
    }

def main():
    try:
        df = pd.read_csv("data/model_ready_features.csv")
    except FileNotFoundError:
        print(json.dumps({"error": "Dataset not found"}))
        return
        
    X = df.drop(columns=["lead_id", "converted"])
    y = df["converted"]
    
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    baseline = RuleBasedBaseline()
    baseline_prob = baseline.predict_proba(X_test)
    
    ml_model = MLModel(artifact_path="data/model.joblib")
    ml_prob = ml_model.predict_probability(X_test)
    
    report = {
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "evaluation_population_size": len(X_test),
        "baseline_model": {
            "name": "RuleBasedBaseline",
            "metrics": calculate_metrics(y_test, baseline_prob)
        },
        "candidate_ml_model": {
            "name": "GradientBoostingClassifier",
            "model_version": ml_model._metadata.get("model_version", "unknown"),
            "metrics": calculate_metrics(y_test, ml_prob)
        }
    }
    
    with open("data/evaluation_comparison.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
