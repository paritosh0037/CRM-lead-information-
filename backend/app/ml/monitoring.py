import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from app.ml.evaluate import evaluate_classification, evaluate_ranking


class ModelMonitor:
    """
    Deterministically monitors ML model performance and data distribution drift.
    """

    def __init__(
        self,
        numerical_drift_threshold: float = 0.1,  # KS-statistic threshold
        categorical_drift_threshold: float = 0.15,  # Total Variation Distance (TVD) threshold
        auc_degradation_threshold: float = 0.65,  # Minimum acceptable ROC-AUC
    ):
        self.num_threshold = numerical_drift_threshold
        self.cat_threshold = categorical_drift_threshold
        self.auc_threshold = auc_degradation_threshold

    def _check_numerical_drift(self, feature_name: str, ref_data: pd.Series, cur_data: pd.Series) -> Dict[str, Any]:
        ref = ref_data.dropna()
        cur = cur_data.dropna()
        
        if len(ref) == 0 or len(cur) == 0:
            return {
                "feature": feature_name,
                "metric": "ks_statistic",
                "metric_value": 0.0,
                "configured_threshold": self.num_threshold,
                "drift_detected": False,
                "reference_statistics": {},
                "current_statistics": {},
                "error": "Insufficient data"
            }
        
        stat, _ = ks_2samp(ref, cur)
        stat = float(stat)
        
        return {
            "feature": feature_name,
            "metric": "ks_statistic",
            "metric_value": stat,
            "configured_threshold": self.num_threshold,
            "drift_detected": stat > self.num_threshold,
            "reference_statistics": {"mean": float(ref.mean()), "std": float(ref.std())},
            "current_statistics": {"mean": float(cur.mean()), "std": float(cur.std())}
        }

    def _check_categorical_drift(self, feature_name: str, ref_data: pd.Series, cur_data: pd.Series) -> Dict[str, Any]:
        ref_counts = ref_data.value_counts(normalize=True)
        cur_counts = cur_data.value_counts(normalize=True)
        
        all_cats = set(ref_counts.index).union(set(cur_counts.index))
        tvd = 0.5 * sum(abs(ref_counts.get(c, 0) - cur_counts.get(c, 0)) for c in all_cats)
        
        return {
            "feature": feature_name,
            "metric": "total_variation_distance",
            "metric_value": float(tvd),
            "configured_threshold": self.cat_threshold,
            "drift_detected": float(tvd) > self.cat_threshold,
            "reference_statistics": ref_counts.to_dict(),
            "current_statistics": cur_counts.to_dict()
        }

    def evaluate_data_drift(
        self, 
        reference_df: pd.DataFrame, 
        current_df: pd.DataFrame, 
        numerical_features: List[str], 
        categorical_features: List[str]
    ) -> Dict[str, Any]:
        """
        Computes drift for numerical and categorical features.
        """
        drift_results = []
        overall_drift_detected = False
        
        for feat in numerical_features:
            if feat in reference_df.columns and feat in current_df.columns:
                res = self._check_numerical_drift(feat, reference_df[feat], current_df[feat])
                drift_results.append(res)
                if res.get("drift_detected", False):
                    overall_drift_detected = True

        for feat in categorical_features:
            if feat in reference_df.columns and feat in current_df.columns:
                res = self._check_categorical_drift(feat, reference_df[feat].astype(str), current_df[feat].astype(str))
                drift_results.append(res)
                if res.get("drift_detected", False):
                    overall_drift_detected = True

        return {
            "overall_drift_detected": overall_drift_detected,
            "features": drift_results
        }

    def evaluate_prediction_drift(
        self, 
        reference_preds: pd.DataFrame, 
        current_preds: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Monitors changes in conversion probability, lead score, and recommendation distributions.
        """
        drift_results = []
        overall_drift_detected = False
        
        # 1. Conversion Probability (Numerical)
        if "conversion_probability" in reference_preds.columns and "conversion_probability" in current_preds.columns:
            res = self._check_numerical_drift(
                "conversion_probability", 
                reference_preds["conversion_probability"], 
                current_preds["conversion_probability"]
            )
            drift_results.append(res)
            if res.get("drift_detected", False):
                overall_drift_detected = True
                
        # 2. Lead Score (Numerical)
        if "lead_score" in reference_preds.columns and "lead_score" in current_preds.columns:
            res = self._check_numerical_drift(
                "lead_score", 
                reference_preds["lead_score"], 
                current_preds["lead_score"]
            )
            drift_results.append(res)
            if res.get("drift_detected", False):
                overall_drift_detected = True

        # 3. Recommendation/Action Distribution (Categorical)
        if "recommended_action" in reference_preds.columns and "recommended_action" in current_preds.columns:
            res = self._check_categorical_drift(
                "recommended_action", 
                reference_preds["recommended_action"], 
                current_preds["recommended_action"]
            )
            drift_results.append(res)
            if res.get("drift_detected", False):
                overall_drift_detected = True

        return {
            "overall_drift_detected": overall_drift_detected,
            "distributions": drift_results
        }

    def evaluate_performance(
        self, 
        y_true: Optional[np.ndarray], 
        y_proba: Optional[np.ndarray]
    ) -> Dict[str, Any]:
        """
        Calculates performance if ground truth is available. Uses existing evaluate.py logic.
        """
        if y_true is None or y_proba is None or len(y_true) == 0:
            return {
                "status": "unavailable",
                "reason": "Ground truth labels not available for the current dataset."
            }

        y_pred = (y_proba >= 0.5).astype(int)
        
        c_metrics = evaluate_classification(y_true, y_pred, y_proba)
        r_metrics = evaluate_ranking(y_true, y_proba)
        
        return {
            "status": "available",
            "classification_metrics": c_metrics,
            "ranking_metrics": r_metrics
        }

    def generate_report(
        self,
        model_version: str,
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame,
        numerical_features: List[str],
        categorical_features: List[str],
        reference_preds: pd.DataFrame,
        current_preds: pd.DataFrame,
        actual_outcomes: Optional[np.ndarray] = None,
        predicted_probs: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Produces the structured monitoring report.
        """
        data_drift = self.evaluate_data_drift(reference_df, current_df, numerical_features, categorical_features)
        pred_drift = self.evaluate_prediction_drift(reference_preds, current_preds)
        perf = self.evaluate_performance(actual_outcomes, predicted_probs)
        
        # Determine Retraining Recommendation
        retraining_recommendation = "NO_ACTION"
        severity = "LOW"
        reasons = []

        # Data drift is an investigation signal
        if data_drift["overall_drift_detected"]:
            reasons.append("Significant data drift detected in feature distributions.")
            retraining_recommendation = "INVESTIGATE"
            severity = "MEDIUM"

        # Prediction drift is an investigation signal
        if pred_drift["overall_drift_detected"]:
            reasons.append("Significant prediction drift detected in model outputs.")
            if retraining_recommendation == "NO_ACTION":
                retraining_recommendation = "INVESTIGATE"
                severity = "MEDIUM"

        # Performance degradation is a strong retrain signal
        if perf["status"] == "available":
            current_auc = perf["classification_metrics"]["roc_auc"]
            if current_auc < self.auc_threshold:
                reasons.append(f"Performance degradation: ROC-AUC {current_auc:.3f} is below threshold {self.auc_threshold}.")
                retraining_recommendation = "RETRAIN_RECOMMENDED"
                severity = "HIGH"

        report = {
            "reference_version": model_version,
            "current_period": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data_drift": data_drift,
            "prediction_drift": pred_drift,
            "overall_drift_detected": data_drift["overall_drift_detected"] or pred_drift["overall_drift_detected"],
            "performance": perf,
            "severity": severity,
            "retraining_recommendation": retraining_recommendation,
            "reasons": reasons
        }
        return report
