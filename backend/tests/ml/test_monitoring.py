import pytest
import numpy as np
import pandas as pd

from app.ml.monitoring import ModelMonitor
from app.ml.evaluate import evaluate_classification, evaluate_ranking

@pytest.fixture
def monitor():
    return ModelMonitor(
        numerical_drift_threshold=0.1,
        categorical_drift_threshold=0.15,
        auc_degradation_threshold=0.65
    )

def test_evaluation_metrics():
    """Test evaluation logic explicitly."""
    y_true = np.array([0, 1, 0, 1, 1])
    y_proba = np.array([0.1, 0.9, 0.4, 0.8, 0.6])
    y_pred = (y_proba >= 0.5).astype(int)

    cls_metrics = evaluate_classification(y_true, y_pred, y_proba)
    assert "roc_auc" in cls_metrics
    assert "f1" in cls_metrics
    assert "brier_score" in cls_metrics
    assert "confusion_matrix" in cls_metrics

    rnk_metrics = evaluate_ranking(y_true, y_proba)
    assert "top_k_metrics" in rnk_metrics
    assert "calibration" in rnk_metrics

def test_no_drift(monitor):
    """Test when reference and current distributions are equivalent."""
    ref_df = pd.DataFrame({"deal_value": np.random.normal(100, 10, 1000)})
    cur_df = pd.DataFrame({"deal_value": np.random.normal(100, 10, 1000)})
    
    drift = monitor.evaluate_data_drift(ref_df, cur_df, ["deal_value"], [])
    assert drift["overall_drift_detected"] is False
    assert drift["features"][0]["drift_detected"] is False

def test_numerical_drift(monitor):
    """Test controlled numerical distribution shift."""
    ref_df = pd.DataFrame({"deal_value": np.random.normal(100, 10, 1000)})
    # Significant shift in mean
    cur_df = pd.DataFrame({"deal_value": np.random.normal(150, 10, 1000)})
    
    drift = monitor.evaluate_data_drift(ref_df, cur_df, ["deal_value"], [])
    assert drift["overall_drift_detected"] is True
    assert drift["features"][0]["drift_detected"] is True

def test_categorical_drift(monitor):
    """Test controlled categorical distribution shift."""
    ref_df = pd.DataFrame({"industry": ["Tech"] * 800 + ["Retail"] * 200})
    cur_df = pd.DataFrame({"industry": ["Tech"] * 200 + ["Retail"] * 800})
    
    drift = monitor.evaluate_data_drift(ref_df, cur_df, [], ["industry"])
    assert drift["overall_drift_detected"] is True
    assert drift["features"][0]["drift_detected"] is True

def test_unseen_category_drift(monitor):
    """Test when current data has categories unseen in reference."""
    ref_df = pd.DataFrame({"industry": ["Tech"] * 1000})
    cur_df = pd.DataFrame({"industry": ["Tech"] * 500 + ["Healthcare"] * 500})
    
    drift = monitor.evaluate_data_drift(ref_df, cur_df, [], ["industry"])
    assert drift["overall_drift_detected"] is True
    assert drift["features"][0]["drift_detected"] is True

def test_prediction_drift(monitor):
    """Test distribution changes in conversion probability and lead score."""
    ref_preds = pd.DataFrame({
        "conversion_probability": np.random.uniform(0, 1, 1000),
        "lead_score": np.random.uniform(0, 100, 1000)
    })
    # Shift towards 1.0 probability
    cur_preds = pd.DataFrame({
        "conversion_probability": np.random.uniform(0.8, 1, 1000),
        "lead_score": np.random.uniform(80, 100, 1000)
    })
    
    drift = monitor.evaluate_prediction_drift(ref_preds, cur_preds)
    assert drift["overall_drift_detected"] is True
    
    features = {d["feature"]: d["drift_detected"] for d in drift["distributions"]}
    assert features["conversion_probability"] is True
    assert features["lead_score"] is True

def test_recommendation_drift(monitor):
    """Test changes in recommended action distribution."""
    ref_preds = pd.DataFrame({"recommended_action": ["CALL"] * 300 + ["EMAIL"] * 250 + ["NURTURE"] * 250 + ["DEMO"] * 150 + ["REVIEW"] * 50})
    cur_preds = pd.DataFrame({"recommended_action": ["CALL"] * 50 + ["EMAIL"] * 200 + ["NURTURE"] * 600 + ["DEMO"] * 100 + ["REVIEW"] * 50})
    
    drift = monitor.evaluate_prediction_drift(ref_preds, cur_preds)
    assert drift["overall_drift_detected"] is True
    
    features = {d["feature"]: d["drift_detected"] for d in drift["distributions"]}
    assert features["recommended_action"] is True

def test_retraining_decision_no_action(monitor):
    """Test state NO_ACTION."""
    ref_df = pd.DataFrame({"val": np.random.normal(0, 1, 100)})
    cur_df = pd.DataFrame({"val": np.random.normal(0, 1, 100)})
    
    ref_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 100)})
    cur_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 100)})
    
    # Perfect performance
    y_true = np.array([0, 1, 0, 1])
    y_proba = np.array([0.1, 0.9, 0.1, 0.9])
    
    report = monitor.generate_report(
        "v1.0", ref_df, cur_df, ["val"], [], ref_preds, cur_preds, y_true, y_proba
    )
    
    assert report["retraining_recommendation"] == "NO_ACTION"
    assert report["severity"] == "LOW"

def test_retraining_decision_investigate(monitor):
    """Test state INVESTIGATE caused by drift."""
    ref_df = pd.DataFrame({"val": np.random.normal(0, 1, 1000)})
    cur_df = pd.DataFrame({"val": np.random.normal(5, 1, 1000)}) # High drift
    
    ref_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 1000)})
    cur_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 1000)})
    
    report = monitor.generate_report(
        "v1.0", ref_df, cur_df, ["val"], [], ref_preds, cur_preds, None, None
    )
    
    assert report["retraining_recommendation"] == "INVESTIGATE"
    assert report["severity"] == "MEDIUM"

def test_retraining_decision_retrain_recommended(monitor):
    """Test state RETRAIN_RECOMMENDED caused by performance degradation."""
    ref_df = pd.DataFrame({"val": np.random.normal(0, 1, 100)})
    cur_df = pd.DataFrame({"val": np.random.normal(0, 1, 100)})
    
    ref_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 100)})
    cur_preds = pd.DataFrame({"conversion_probability": np.random.uniform(0, 1, 100)})
    
    # Terrible performance (worse than random) -> AUC < 0.65
    y_true = np.array([0, 1, 0, 1])
    y_proba = np.array([0.9, 0.1, 0.9, 0.1])
    
    report = monitor.generate_report(
        "v1.0", ref_df, cur_df, ["val"], [], ref_preds, cur_preds, y_true, y_proba
    )
    
    assert report["retraining_recommendation"] == "RETRAIN_RECOMMENDED"
    assert report["severity"] == "HIGH"
