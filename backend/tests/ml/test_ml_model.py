import pytest
import pandas as pd
import numpy as np
import tempfile
import os

from app.ml.train import run_training_pipeline, train_candidate_models
from app.ml.baseline import RuleBasedBaseline
from app.ml.model import MLModel

@pytest.fixture
def mock_dataset():
    """Generates a small controlled dataset for testing."""
    return pd.DataFrame({
        "lead_id": [f"L{i}" for i in range(100)],
        "converted": np.random.choice([0, 1], size=100),
        "demo_requested": np.random.choice([0, 1], size=100),
        "deal_value": np.random.uniform(1000, 100000, size=100),
        "email_clicked": np.random.randint(0, 10, size=100)
    })

def test_model_training_completes(mock_dataset):
    with tempfile.TemporaryDirectory() as temp_dir:
        model, summary, preds = run_training_pipeline(
            output_dir=temp_dir,
            test_size=0.2,
            random_state=42,
            df=mock_dataset
        )
        assert model is not None
        assert summary["champion_model"] == "GradientBoosting"
        assert len(preds) == 20

def test_probability_output_bounds(mock_dataset):
    with tempfile.TemporaryDirectory() as temp_dir:
        model, _, preds = run_training_pipeline(output_dir=temp_dir, df=mock_dataset)
        assert (preds["conversion_probability"] >= 0.0).all()
        assert (preds["conversion_probability"] <= 1.0).all()

def test_determinism(mock_dataset):
    """Same dataset, split, random seed = same behavior."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model1, summary1, preds1 = run_training_pipeline(output_dir=temp_dir, random_state=42, df=mock_dataset)
        model2, summary2, preds2 = run_training_pipeline(output_dir=temp_dir, random_state=42, df=mock_dataset)
        
        assert np.allclose(preds1["conversion_probability"], preds2["conversion_probability"])

def test_target_exclusion(mock_dataset):
    """Verify target 'converted' cannot enter the feature matrix."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model, summary, _ = run_training_pipeline(output_dir=temp_dir, df=mock_dataset)
        
        # Access the loaded model features
        ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
        features = ml_model._metadata["feature_names"]
        
        assert "converted" not in features
        assert "lead_id" not in features

def test_persistence_and_consistency(mock_dataset):
    """Verify save/load and loaded model consistency."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model, _, _ = run_training_pipeline(output_dir=temp_dir, df=mock_dataset)
        
        X = mock_dataset.drop(columns=["lead_id", "converted"])
        original_proba = model.predict_proba(X)[:, 1]
        
        ml_model = MLModel(artifact_path=os.path.join(temp_dir, "model.joblib"))
        loaded_proba = ml_model.predict_probability(X)
        
        assert np.allclose(original_proba, loaded_proba)

def test_baseline_comparison(mock_dataset):
    """Verify both Baseline and ML model can be evaluated on the same data."""
    X = mock_dataset.drop(columns=["lead_id", "converted"])
    
    baseline = RuleBasedBaseline()
    base_proba = baseline.predict_proba(X)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        model, _, _ = run_training_pipeline(output_dir=temp_dir, df=mock_dataset)
        ml_proba = model.predict_proba(X)[:, 1]
        
        # Both must return valid probabilities for the exact same input DataFrame
        assert len(base_proba) == len(ml_proba) == len(X)
