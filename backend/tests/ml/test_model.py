import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.ml.baseline import split_data
from app.ml.engine import MLEngine
from app.ml.train import evaluate_models, run_training_pipeline, train_candidate_models


@pytest.fixture
def sample_dataset():
    data_path = "data/model_ready_features.csv"
    return pd.read_csv(data_path)


def test_train_candidate_models(sample_dataset):
    X_train, X_test, y_train, y_test, _, _ = split_data(
        sample_dataset, test_size=0.2, random_state=42
    )
    models = train_candidate_models(X_train, y_train, random_state=42)

    assert "LogisticRegression" in models
    assert "RandomForest" in models
    assert "GradientBoosting" in models

    eval_results = evaluate_models(models, X_test, y_test)
    for name in models:
        assert "classification_metrics" in eval_results[name]
        assert "ranking_metrics" in eval_results[name]
        assert "roc_auc" in eval_results[name]["classification_metrics"]


def test_run_training_pipeline_artifacts(tmp_path, sample_dataset):
    champion, metrics_summary, preds_df = run_training_pipeline(
        data_path="data/model_ready_features.csv",
        output_dir=str(tmp_path),
        test_size=0.2,
        random_state=42,
    )

    # 1. Model Artifact Saved and Re-loadable
    model_file = tmp_path / "model.joblib"
    assert model_file.exists()

    engine = MLEngine(model_path=str(model_file))
    assert engine.model is not None
    assert engine.model_name == "GradientBoosting"

    # 2. Predictions Dataset Saved
    preds_file = tmp_path / "predictions.csv"
    assert preds_file.exists()
    assert len(preds_df) == 600
    assert "lead_id" in preds_df.columns
    assert "conversion_probability" in preds_df.columns
    assert "lead_score" in preds_df.columns
    assert "converted" in preds_df.columns

    # 3. Probability and Lead Score Value Ranges
    proba = preds_df["conversion_probability"].values
    scores = preds_df["lead_score"].values
    assert np.all((proba >= 0.0) & (proba <= 1.0))
    assert np.all((scores >= 0) & (scores <= 100))
    # Verify Lead Score = Conversion Probability * 100 relationship
    assert np.all(scores == np.round(proba * 100).astype(int))

    # 4. Metrics & Comparison Files Saved
    metrics_file = tmp_path / "model_metrics.json"
    assert metrics_file.exists()
    with open(metrics_file) as f:
        metrics_data = json.load(f)
    assert metrics_data["champion_model"] == "GradientBoosting"
    assert "classification_metrics" in metrics_data
    assert "ranking_metrics" in metrics_data


def test_ml_engine_single_lead_and_batch_prediction(sample_dataset):
    # Train pipeline to ensure model artifact exists
    run_training_pipeline(
        data_path="data/model_ready_features.csv",
        output_dir="data",
        test_size=0.2,
        random_state=42,
    )

    engine = MLEngine(model_path="data/model.joblib")

    # Single lead prediction
    single_record = sample_dataset.iloc[0].to_dict()
    res = engine.predict_lead(single_record)
    assert "conversion_probability" in res
    assert "lead_score" in res
    assert 0.0 <= res["conversion_probability"] <= 1.0
    assert 0 <= res["lead_score"] <= 100

    # Batch prediction
    batch_res = engine.predict_batch(sample_dataset.head(10))
    assert len(batch_res) == 10
    assert "lead_id" in batch_res.columns
    assert "conversion_probability" in batch_res.columns
    assert "lead_score" in batch_res.columns


def test_target_and_sensitive_attributes_exclusion(sample_dataset):
    engine = MLEngine(model_path="data/model.joblib")

    # Prepare DataFrame with target and sensitive attributes deliberately present
    dirty_df = sample_dataset.head(5).copy()
    dirty_df["gender"] = "Female"
    dirty_df["race"] = "TestRace"

    # Should safely clean features without error
    proba = engine.predict_proba(dirty_df)
    assert len(proba) == 5
    assert np.all((proba >= 0.0) & (proba <= 1.0))


def test_training_reproducibility():
    _, sum1, _ = run_training_pipeline(
        data_path="data/model_ready_features.csv",
        output_dir="data",
        test_size=0.2,
        random_state=42,
    )
    _, sum2, _ = run_training_pipeline(
        data_path="data/model_ready_features.csv",
        output_dir="data",
        test_size=0.2,
        random_state=42,
    )

    assert (
        sum1["classification_metrics"]["roc_auc"]
        == sum2["classification_metrics"]["roc_auc"]
    )
    assert sum1["classification_metrics"]["f1"] == sum2["classification_metrics"]["f1"]
