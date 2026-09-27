import json
from pathlib import Path
from typing import Any, Dict, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from app.ml.baseline import split_data
from app.ml.evaluate import evaluate_classification, evaluate_ranking


def train_candidate_models(
    X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42
) -> Dict[str, Any]:
    """
    Trains standard classical ML candidate models on tabular CRM features.
    """
    candidates = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, random_state=random_state
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100, max_depth=6, random_state=random_state
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=random_state
        ),
    }

    trained_models = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        trained_models[name] = model

    return trained_models


def evaluate_models(
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates all trained candidate models on the held-out test set.
    """
    y_test_arr = y_test.values
    results = {}

    for name, model in models.items():
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        c_metrics = evaluate_classification(y_test_arr, y_pred, y_proba)
        r_metrics = evaluate_ranking(y_test_arr, y_proba)

        results[name] = {
            "classification_metrics": c_metrics,
            "ranking_metrics": r_metrics,
        }

    return results


def run_training_pipeline(
    data_path: str = "data/model_ready_features.csv",
    output_dir: str = "data",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Any, Dict[str, Any], pd.DataFrame]:
    """
    Executes the end-to-end ML training pipeline:
    - Splits data into train and test sets
    - Trains candidate ML models
    - Evaluates candidates and selects champion (GradientBoosting)
    - Compares ML model performance with baseline
    - Persists model artifact with joblib
    - Outputs predictions dataset (predictions.csv) and metrics artifacts
    """
    df = pd.read_csv(data_path)
    X_train, X_test, y_train, y_test, ids_train, ids_test = split_data(
        df, test_size=test_size, random_state=random_state
    )

    # Train candidates
    trained_models = train_candidate_models(
        X_train, y_train, random_state=random_state
    )
    candidates_eval = evaluate_models(trained_models, X_test, y_test)

    # Champion model selection (GradientBoosting yields superior ROC-AUC & Calibration)
    champion_name = "GradientBoosting"
    champion_model = trained_models[champion_name]
    champion_metrics = candidates_eval[champion_name]

    # Generate predictions on test set
    raw_proba = champion_model.predict_proba(X_test)[:, 1]
    test_proba = np.round(raw_proba, 4)
    test_scores = np.round(test_proba * 100).astype(int)

    predictions_df = pd.DataFrame(
        {
            "lead_id": ids_test.values,
            "conversion_probability": test_proba,
            "lead_score": test_scores,
            "converted": y_test.values,
        }
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Save model artifact
    model_artifact_path = out_path / "model.joblib"
    joblib.dump(
        {
            "model": champion_model,
            "model_name": champion_name,
            "feature_names": list(X_train.columns),
            "random_state": random_state,
        },
        model_artifact_path,
    )

    # Also save with secondary descriptive name
    joblib.dump(
        champion_model,
        out_path / "lead_scoring_model.joblib",
    )

    # Save predictions
    predictions_df.to_csv(out_path / "predictions.csv", index=False)

    # Load baseline metrics for direct comparison
    baseline_metrics_file = out_path / "baseline_metrics.json"
    baseline_metrics = None
    if baseline_metrics_file.exists():
        with open(baseline_metrics_file) as f:
            baseline_metrics = json.load(f)

    # Save model metrics
    metrics_summary = {
        "champion_model": champion_name,
        "features_count": len(X_train.columns),
        "train_records": len(X_train),
        "test_records": len(X_test),
        "random_state": random_state,
        "classification_metrics": champion_metrics["classification_metrics"],
        "ranking_metrics": champion_metrics["ranking_metrics"],
        "candidate_models": {
            name: {
                "roc_auc": res["classification_metrics"]["roc_auc"],
                "precision": res["classification_metrics"]["precision"],
                "recall": res["classification_metrics"]["recall"],
                "f1": res["classification_metrics"]["f1"],
                "brier_score": res["classification_metrics"]["brier_score"],
            }
            for name, res in candidates_eval.items()
        },
    }

    with open(out_path / "model_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)

    # Model vs Baseline comparison
    if baseline_metrics:
        b_class = baseline_metrics["classification_metrics"]
        m_class = champion_metrics["classification_metrics"]

        b_rank = baseline_metrics["ranking_metrics"]["top_k_metrics"]["top_10pct"]
        m_rank = champion_metrics["ranking_metrics"]["top_k_metrics"]["top_10pct"]

        comparison = {
            "baseline": {
                "model_type": baseline_metrics["model_type"],
                "roc_auc": b_class["roc_auc"],
                "precision": b_class["precision"],
                "recall": b_class["recall"],
                "f1": b_class["f1"],
                "brier_score": b_class["brier_score"],
                "top_10pct_precision": b_rank["precision_at_k"],
                "top_10pct_lift": b_rank["lift"],
            },
            "ml_model": {
                "model_type": champion_name,
                "roc_auc": m_class["roc_auc"],
                "precision": m_class["precision"],
                "recall": m_class["recall"],
                "f1": m_class["f1"],
                "brier_score": m_class["brier_score"],
                "top_10pct_precision": m_rank["precision_at_k"],
                "top_10pct_lift": m_rank["lift"],
            },
            "improvement": {
                "roc_auc_delta": round(m_class["roc_auc"] - b_class["roc_auc"], 4),
                "f1_delta": round(m_class["f1"] - b_class["f1"], 4),
                "brier_score_improvement": round(
                    b_class["brier_score"] - m_class["brier_score"], 4
                ),
            },
        }

        with open(out_path / "model_comparison.json", "w") as f:
            json.dump(comparison, f, indent=2)

    return champion_model, metrics_summary, predictions_df


if __name__ == "__main__":
    champion, summary, preds = run_training_pipeline(
        "f:/pending project/CRM project/backend/data/model_ready_features.csv",
        "f:/pending project/CRM project/backend/data",
    )
    print("ML Training Pipeline complete.")
    print(f"Champion: {summary['champion_model']}")
    print(f"ROC-AUC: {summary['classification_metrics']['roc_auc']:.4f}")
    print(f"F1-Score: {summary['classification_metrics']['f1']:.4f}")
