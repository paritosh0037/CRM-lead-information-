import numpy as np
import pytest
from app.ml.evaluate import evaluate_classification, evaluate_ranking

def test_evaluate_classification():
    y_true = np.array([0, 1, 0, 1, 0, 0, 1, 1, 1, 0])
    y_pred = np.array([0, 1, 0, 0, 0, 1, 1, 1, 1, 0])
    y_proba = np.array([0.1, 0.9, 0.2, 0.4, 0.3, 0.8, 0.7, 0.6, 0.9, 0.1])
    
    res = evaluate_classification(y_true, y_pred, y_proba)
    
    assert "roc_auc" in res
    assert "precision" in res
    assert "recall" in res
    assert "f1" in res
    assert "brier_score" in res
    assert "confusion_matrix" in res
    
    cm = res["confusion_matrix"]
    assert cm["tn"] == 4
    assert cm["fp"] == 1
    assert cm["fn"] == 1
    assert cm["tp"] == 4


def test_evaluate_ranking():
    y_true = np.array([0, 1, 0, 1, 0, 0, 1, 1, 1, 0])
    y_proba = np.array([0.1, 0.9, 0.2, 0.4, 0.3, 0.8, 0.7, 0.6, 0.9, 0.1])
    
    res = evaluate_ranking(y_true, y_proba, k_fractions=[0.2, 0.5])
    
    assert "overall_conversion_rate" in res
    assert res["overall_conversion_rate"] == 0.5
    
    assert "top_k_metrics" in res
    assert "top_20pct" in res["top_k_metrics"]
    assert "top_50pct" in res["top_k_metrics"]
    
    assert res["top_k_metrics"]["top_20pct"]["conversions"] == 2
    
    assert "score_buckets" in res
    assert "calibration" in res
    assert "calibration_curve" in res["calibration"]
