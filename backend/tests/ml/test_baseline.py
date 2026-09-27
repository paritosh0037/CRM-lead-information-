import json
import numpy as np
import pandas as pd
import pytest

from app.ml.baseline import (
    RuleBasedBaseline,
    evaluate_classification,
    evaluate_ranking,
    run_baseline_pipeline,
    split_data,
)


@pytest.fixture
def sample_features_df():
    """
    Creates a small synthetic dataset formatted like model_ready_features.csv for testing.
    """
    np.random.seed(42)
    n = 100
    df = pd.DataFrame(
        {
            "lead_id": [f"L{i:05d}" for i in range(1, n + 1)],
            "annual_revenue": np.random.uniform(100000, 1000000, n),
            "budget": np.random.uniform(5000, 50000, n),
            "deal_value": np.random.uniform(1000, 20000, n),
            "previous_purchase": np.random.choice([0, 1], n),
            "days_since_last_contact": np.random.randint(0, 180, n),
            "email_opened": np.random.randint(0, 10, n),
            "email_clicked": np.random.randint(0, 5, n),
            "call_made": np.random.randint(0, 5, n),
            "web_visit": np.random.randint(0, 10, n),
            "pricing_page_visit": np.random.randint(0, 5, n),
            "demo_requested": np.random.choice([0, 1], n, p=[0.7, 0.3]),
            "total_web_duration": np.random.randint(0, 1000, n),
            "total_interactions": np.random.randint(0, 25, n),
            "opportunity_stage_Qualified": np.random.choice([0, 1], n),
            "opportunity_stage_Proposal": np.random.choice([0, 1], n),
            "converted": np.random.choice([0, 1], n, p=[0.6, 0.4]),
        }
    )
    return df


def test_split_data_dimensions_and_separation(sample_features_df):
    X_train, X_test, y_train, y_test, ids_train, ids_test = split_data(
        sample_features_df, test_size=0.2, random_state=42
    )

    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20
    assert len(ids_train) == 80
    assert len(ids_test) == 20

    # Ensure target and IDs are not in feature matrix
    assert "converted" not in X_train.columns
    assert "converted" not in X_test.columns
    assert "lead_id" not in X_train.columns
    assert "lead_id" not in X_test.columns

    # Check intersection of train and test IDs is empty
    assert len(set(ids_train).intersection(set(ids_test))) == 0


def test_baseline_predictions_validity(sample_features_df):
    X_train, X_test, y_train, y_test, _, _ = split_data(
        sample_features_df, test_size=0.2, random_state=42
    )
    baseline = RuleBasedBaseline()

    proba = baseline.predict_proba(X_test)
    preds = baseline.predict(X_test, threshold=0.5)
    scores = baseline.score(X_test)

    assert len(proba) == len(X_test)
    assert len(preds) == len(X_test)
    assert len(scores) == len(X_test)

    # Check value ranges
    assert np.all((proba >= 0.0) & (proba <= 1.0))
    assert np.all(np.isin(preds, [0, 1]))
    assert np.all((scores >= 0) & (scores <= 100))


def test_evaluate_classification_metrics():
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    y_proba = np.array([0.9, 0.1, 0.8, 0.7, 0.2, 0.4, 0.6, 0.3])
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = evaluate_classification(y_true, y_pred, y_proba)

    assert "roc_auc" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "brier_score" in metrics
    assert "confusion_matrix" in metrics

    cm = metrics["confusion_matrix"]
    assert cm["tp"] == 4
    assert cm["tn"] == 4
    assert cm["fp"] == 0
    assert cm["fn"] == 0
    assert metrics["roc_auc"] == 1.0


def test_evaluate_ranking_metrics():
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 0, 0, 0])  # 4 positives out of 10 (40%)
    y_proba = np.array([0.95, 0.85, 0.80, 0.75, 0.60, 0.45, 0.30, 0.20, 0.15, 0.05])

    metrics = evaluate_ranking(y_true, y_proba, k_fractions=[0.2, 0.4])

    assert "overall_conversion_rate" in metrics
    assert metrics["overall_conversion_rate"] == 0.4

    # Top 20% = top 2 leads ([1, 0] -> 1 positive) -> Precision@20% = 0.5
    top_20 = metrics["top_k_metrics"]["top_20pct"]
    assert top_20["leads_count"] == 2
    assert top_20["conversions"] == 1
    assert top_20["precision_at_k"] == 0.5
    assert top_20["lift"] == pytest.approx(0.5 / 0.4)

    # Score buckets verification
    assert "score_buckets" in metrics
    assert "0-20" in metrics["score_buckets"]
    assert "80-100" in metrics["score_buckets"]

    # Calibration verification
    assert "calibration" in metrics
    assert "mean_predicted_probability" in metrics["calibration"]


def test_baseline_pipeline_execution_and_reproducibility(tmp_path):
    # Test execution on real dataset
    data_path = "data/model_ready_features.csv"
    res1 = run_baseline_pipeline(
        data_path=data_path, output_dir=str(tmp_path), test_size=0.2, random_state=42
    )
    res2 = run_baseline_pipeline(
        data_path=data_path, output_dir=str(tmp_path), test_size=0.2, random_state=42
    )

    assert res1["classification_metrics"] == res2["classification_metrics"]
    assert res1["ranking_metrics"] == res2["ranking_metrics"]

    # Verify JSON file artifact saved
    artifact_file = tmp_path / "baseline_metrics.json"
    assert artifact_file.exists()

    with open(artifact_file) as f:
        data = json.load(f)
    assert data["model_type"] == "RuleBasedBaseline"
    assert data["total_records"] == 3000
    assert data["test_records"] == 600


def test_no_sensitive_attributes_used():
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    df = pd.read_csv("data/model_ready_features.csv")
    for attr in sensitive_attrs:
        assert attr not in df.columns
