import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from scipy.special import expit

from app.ml.train import run_training_pipeline
from app.ml.model import MLModel

@pytest.fixture(scope="module")
def trained_model_env():
    """Generates a dataset, trains a model, and returns a temp dir with artifacts."""
    df = pd.DataFrame({
        "lead_id": [f"L{i}" for i in range(100)],
        "converted": np.random.choice([0, 1], size=100),
        "demo_requested": np.random.choice([0, 1], size=100),
        "deal_value": np.random.uniform(1000, 100000, size=100),
        "email_clicked": np.random.randint(0, 10, size=100),
        "industry_Technology": np.random.choice([0, 1], size=100)
    })
    
    temp_dir = tempfile.mkdtemp()
    model, summary, preds = run_training_pipeline(
        output_dir=temp_dir,
        test_size=0.2,
        random_state=42,
        df=df
    )
    
    X_test = df.drop(columns=["lead_id", "converted"]).head(5)
    return temp_dir, X_test

def test_shap_availability(trained_model_env):
    temp_dir, X_test = trained_model_env
    ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
    assert ml_model._explainer is not None, "SHAP explainer should be initialized"

def test_explanation_structure_and_sanity(trained_model_env):
    temp_dir, X_test = trained_model_env
    ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
    
    # Test on a single lead (e.g., hot lead archetype)
    single_lead = X_test.iloc[[0]]
    explanation = ml_model.explain(single_lead)
    
    # Check structure
    assert "prediction_probability" in explanation
    assert "margin_prediction" in explanation
    assert "base_value" in explanation
    assert "top_positive_factors" in explanation
    assert "top_negative_factors" in explanation
    assert "human_readable" in explanation
    
    # Check contribution sanity: base_value + sum(shap) ≈ margin
    sum_shap = sum(f["shap_value"] for f in explanation["top_positive_factors"] + explanation["top_negative_factors"])
    margin = explanation["base_value"] + sum_shap
    assert abs(margin - explanation["margin_prediction"]) < 1e-4
    
    # Check prediction consistency: expit(margin) ≈ proba for GBC
    calc_proba = expit(margin)
    assert abs(calc_proba - explanation["prediction_probability"]) < 1e-3
    
    # Check sorting (absolute descending)
    pos = explanation["top_positive_factors"]
    if len(pos) > 1:
        assert abs(pos[0]["shap_value"]) >= abs(pos[1]["shap_value"])
        
    neg = explanation["top_negative_factors"]
    if len(neg) > 1:
        assert abs(neg[0]["shap_value"]) >= abs(neg[1]["shap_value"])

def test_explanation_determinism(trained_model_env):
    temp_dir, X_test = trained_model_env
    ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
    
    single_lead = X_test.iloc[[0]]
    exp1 = ml_model.explain(single_lead)
    exp2 = ml_model.explain(single_lead)
    
    assert exp1["prediction_probability"] == exp2["prediction_probability"]
    assert exp1["margin_prediction"] == exp2["margin_prediction"]
    assert exp1["human_readable"] == exp2["human_readable"]

def test_explain_multiple_rows_fails(trained_model_env):
    temp_dir, X_test = trained_model_env
    ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
    
    with pytest.raises(ValueError, match="exactly one lead"):
        ml_model.explain(X_test)  # passing multiple rows

def test_missing_features_fails(trained_model_env):
    temp_dir, X_test = trained_model_env
    ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
    
    bad_lead = X_test.iloc[[0]].drop(columns=["demo_requested"])
    with pytest.raises(ValueError, match="Missing required features"):
        ml_model.explain(bad_lead)
