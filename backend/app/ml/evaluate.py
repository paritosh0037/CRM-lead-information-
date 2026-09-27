import json
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classification(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray
) -> Dict[str, Any]:
    """
    Calculate classification metrics: ROC-AUC, Precision, Recall, F1, Confusion Matrix, Brier Score.
    """
    cm = confusion_matrix(y_true, y_pred)
    # Handle cases where confusion matrix might not be 2x2 if only one class is predicted
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        # Fallback if there's only one class in y_true/y_pred
        tn = fp = fn = tp = 0
        if len(np.unique(y_true)) == 1:
            if y_true[0] == 0:
                tn = cm[0, 0]
            else:
                tp = cm[0, 0]

    return {
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, y_proba)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def evaluate_ranking(
    y_true: np.ndarray, y_proba: np.ndarray, k_fractions: List[float] = [0.1, 0.2, 0.3]
) -> Dict[str, Any]:
    """
    Calculate ranking-oriented metrics: Precision@K, Recall@K, Top-K conversion rate, Lift,
    Conversion rate by score bucket, and Calibration curve.
    """
    n_samples = len(y_true)
    overall_conversion_rate = float(np.mean(y_true))
    total_positives = int(np.sum(y_true))

    # Sort descending by predicted probability
    order = np.argsort(-y_proba)
    y_sorted = y_true[order]
    y_proba_sorted = y_proba[order]

    top_k_metrics = {}
    for k in k_fractions:
        top_n = max(1, int(np.ceil(k * n_samples)))
        top_positives = int(np.sum(y_sorted[:top_n]))

        precision_at_k = float(top_positives / top_n)
        recall_at_k = float(top_positives / total_positives) if total_positives > 0 else 0.0
        lift = float(precision_at_k / overall_conversion_rate) if overall_conversion_rate > 0 else 0.0

        k_pct_key = f"top_{int(k * 100)}pct"
        top_k_metrics[k_pct_key] = {
            "k_fraction": k,
            "leads_count": top_n,
            "conversions": top_positives,
            "precision_at_k": precision_at_k,
            "recall_at_k": recall_at_k,
            "top_k_conversion_rate": precision_at_k,
            "lift": lift,
        }

    # Score buckets (0-20, 20-40, 40-60, 60-80, 80-100)
    scores = np.round(y_proba * 100)
    bucket_edges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    score_buckets = {}

    for low, high in bucket_edges:
        if high == 100:
            mask = (scores >= low) & (scores <= high)
        else:
            mask = (scores >= low) & (scores < high)

        count = int(np.sum(mask))
        conv = int(np.sum(y_true[mask])) if count > 0 else 0
        rate = float(conv / count) if count > 0 else 0.0

        bucket_key = f"{low}-{high}"
        score_buckets[bucket_key] = {
            "lead_count": count,
            "conversion_count": conv,
            "conversion_rate": rate,
        }

    # Decile calibration curve
    deciles = np.array_split(np.arange(n_samples), 10)
    calibration_curve = []
    for d_idx in deciles:
        if len(d_idx) == 0:
            continue
        actual_rate = float(np.mean(y_sorted[d_idx]))
        expected_rate = float(np.mean(y_proba_sorted[d_idx]))
        calibration_curve.append({
            "expected": expected_rate,
            "actual": actual_rate,
            "count": len(d_idx)
        })

    calibration = {
        "mean_predicted_probability": float(np.mean(y_proba)),
        "actual_conversion_rate": overall_conversion_rate,
        "calibration_gap": float(np.mean(y_proba) - overall_conversion_rate),
        "calibration_curve": calibration_curve
    }

    return {
        "overall_conversion_rate": overall_conversion_rate,
        "top_k_metrics": top_k_metrics,
        "score_buckets": score_buckets,
        "calibration": calibration,
    }


def generate_evaluation_artifacts(
    predictions_path: str = "data/predictions.csv",
    output_dir: str = "data"
) -> Dict[str, Any]:
    """
    Load predictions, calculate metrics, and save evaluation artifacts.
    """
    df = pd.read_csv(predictions_path)
    
    y_true = df["converted"].values
    y_proba = df["conversion_probability"].values
    y_pred = (y_proba >= 0.5).astype(int)

    c_metrics = evaluate_classification(y_true, y_pred, y_proba)
    r_metrics = evaluate_ranking(y_true, y_proba)
    
    evaluation_results = {
        "classification_metrics": c_metrics,
        "ranking_metrics": r_metrics
    }
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "evaluation_metrics.json", "w") as f:
        json.dump(evaluation_results, f, indent=2)
        
    return evaluation_results


if __name__ == "__main__":
    import sys
    base_dir = Path(__file__).resolve().parent.parent.parent
    pred_path = base_dir / "data" / "predictions.csv"
    out_dir = base_dir / "data"
    generate_evaluation_artifacts(str(pred_path), str(out_dir))
    print("Evaluation artifacts generated.")
