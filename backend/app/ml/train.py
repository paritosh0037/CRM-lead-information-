import json
import datetime
from pathlib import Path
from typing import Any, Dict, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

from app.ml.evaluate import evaluate_classification, evaluate_ranking


def split_data(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Splits dataset into train and test sets.
    
    LIMITATION DOCUMENTATION: Time-Aware Splitting
    ----------------------------------------------
    The dataset (leads.csv / model_ready_features.csv) does not contain a `created_at`, 
    `conversion_date`, or sufficient lead-level temporal milestones to implement a 
    proper out-of-time (OOT) validation split.
    
    Per Phase 4 instructions: We stop attempting a temporal split and explicitly 
    document this limitation. We are falling back to a stratified random split 
    until the upstream data engineering team provides lead lifecycle timestamps.
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


def train_candidate_models(
    X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42
) -> Dict[str, Any]:
    """
    Trains the Phase 4 candidate ML model: GradientBoostingClassifier.
    """
    # Using the required Phase 4 hyperparameters
    model = GradientBoostingClassifier(
        n_estimators=100, 
        max_depth=4, 
        learning_rate=0.1, 
        random_state=random_state
    )

    model.fit(X_train, y_train)
    return {"GradientBoosting": model}


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
    df: pd.DataFrame = None,
) -> Tuple[Any, Dict[str, Any], pd.DataFrame]:
    """
    Executes the end-to-end Phase 4 ML training pipeline.
    """
    if df is None:
        df = pd.read_csv(data_path)
        
    X_train, X_test, y_train, y_test, ids_train, ids_test = split_data(
        df, test_size=test_size, random_state=random_state
    )

    # Train candidates
    trained_models = train_candidate_models(
        X_train, y_train, random_state=random_state
    )
    candidates_eval = evaluate_models(trained_models, X_test, y_test)

    # Champion model selection
    champion_name = "GradientBoosting"
    champion_model = trained_models[champion_name]
    champion_metrics = candidates_eval[champion_name]

    # Generate predictions on test set
    raw_proba = champion_model.predict_proba(X_test)[:, 1]
    test_proba = np.round(raw_proba, 4)
    # Lead score maps ML probability to 0-100 directly
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

    # Structured Model Metadata Artifact
    model_metadata = {
        "model_name": champion_name,
        "model_version": "1.0.0",
        "algorithm": "GradientBoostingClassifier",
        "target": "converted",
        "feature_contract_version": "v2_phase2",
        "training_data_period": "unknown_no_temporal_features",
        "evaluation_data_period": "unknown_no_temporal_features",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
            "random_state": random_state
        },
        "metrics": {
            "roc_auc": champion_metrics["classification_metrics"]["roc_auc"],
            "brier_score": champion_metrics["classification_metrics"]["brier_score"]
        },
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "feature_names": list(X_train.columns)
    }

    # Save model artifact via joblib including metadata
    model_artifact_path = out_path / "model.joblib"
    joblib.dump(
        {
            "model": champion_model,
            "metadata": model_metadata
        },
        model_artifact_path,
    )

    # Save metadata JSON explicitly for monitoring
    with open(out_path / "model_metadata.json", "w") as f:
        json.dump(model_metadata, f, indent=2)

    # Save predictions
    predictions_df.to_csv(out_path / "ml_predictions.csv", index=False)

    # Load baseline metrics for direct comparison
    baseline_metrics_file = out_path / "baseline_metrics.json"
    baseline_metrics = None
    if baseline_metrics_file.exists():
        with open(baseline_metrics_file) as f:
            baseline_metrics = json.load(f)

    # Save ML model metrics
    metrics_summary = {
        "champion_model": champion_name,
        "features_count": len(X_train.columns),
        "train_records": len(X_train),
        "test_records": len(X_test),
        "random_state": random_state,
        "classification_metrics": champion_metrics["classification_metrics"],
        "ranking_metrics": champion_metrics["ranking_metrics"]
    }

    with open(out_path / "ml_metrics.json", "w") as f:
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

        with open(out_path / "model_vs_baseline_comparison.json", "w") as f:
            json.dump(comparison, f, indent=2)

    return champion_model, metrics_summary, predictions_df


if __name__ == "__main__":
    champion, summary, preds = run_training_pipeline(
        "f:/pending project/CRM project/backend/data/model_ready_features.csv",
        "f:/pending project/CRM project/backend/data",
    )
    print("Phase 4 ML Training Pipeline complete.")
    print(f"Champion: {summary['champion_model']}")
    print(f"ROC-AUC: {summary['classification_metrics']['roc_auc']:.4f}")
    print(f"F1-Score: {summary['classification_metrics']['f1']:.4f}")
