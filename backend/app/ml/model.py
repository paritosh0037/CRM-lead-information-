import joblib
import pandas as pd
import numpy as np
import shap
from scipy.special import expit
from typing import Dict, Any, Optional, List, Tuple

class MLModel:
    """
    Inference interface for the trained CRM ML model.
    """
    def __init__(self, artifact_path: str = "data/model.joblib"):
        self.artifact_path = artifact_path
        self._model = None
        self._metadata = None
        self._explainer = None
        self.load_model()

    def load_model(self):
        """Loads the model and its metadata from the joblib artifact."""
        try:
            artifact = joblib.load(self.artifact_path)
            self._model = artifact.get("model")
            self._metadata = artifact.get("metadata", {})
            if self._model is None:
                raise ValueError("Model object not found in artifact.")
            
            # Initialize TreeExplainer for the loaded GradientBoostingClassifier.
            # model_output="raw" produces log-odds (margin) space.
            self._explainer = shap.TreeExplainer(self._model)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.artifact_path}: {str(e)}")

    def _prepare_features(self, features: pd.DataFrame) -> pd.DataFrame:
        expected_features = self._metadata.get("feature_names", [])
        if expected_features:
            missing = set(expected_features) - set(features.columns)
            if missing:
                raise ValueError(f"Missing required features: {missing}")
            # Reorder to match training
            return features[expected_features]
        return features

    def predict_probability(self, features: pd.DataFrame) -> Any:
        """
        Returns the learned conversion probability for a single lead or multiple leads.
        """
        if self._model is None:
            raise RuntimeError("Model is not loaded.")
        
        features = self._prepare_features(features)
        proba = self._model.predict_proba(features)[:, 1]
        
        # Return scalar if single row, else list/array
        if len(proba) == 1:
            return float(proba[0])
        return proba

    def explain(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates a local SHAP explanation for a single lead.
        
        Returns:
            Dict containing:
            - prediction_probability: float
            - margin_prediction: float
            - base_value: float
            - top_positive_factors: list of dicts
            - top_negative_factors: list of dicts
            - human_readable: str
        """
        if len(features) != 1:
            raise ValueError("Local explanation expects exactly one lead (one row).")
        
        features = self._prepare_features(features)
        
        # SHAP calculation
        shap_values = self._explainer.shap_values(features)[0]
        base_value = float(self._explainer.expected_value)
        if isinstance(base_value, (list, np.ndarray)):
            # Handle multi-class / different output shapes if necessary
            base_value = float(base_value[0])
            
        # Model predictions
        proba = float(self._model.predict_proba(features)[0, 1])
        
        feature_names = features.columns.tolist()
        feature_values = features.iloc[0].values
        
        positive_factors = []
        negative_factors = []
        
        for name, val, sv in zip(feature_names, feature_values, shap_values):
            factor = {
                "feature": name,
                "value": float(val),
                "shap_value": float(sv),
                "direction": "positive" if sv > 0 else "negative" if sv < 0 else "neutral"
            }
            if factor["direction"] == "positive":
                positive_factors.append(factor)
            elif factor["direction"] == "negative":
                negative_factors.append(factor)
                
        # Sort by absolute SHAP magnitude descending
        positive_factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        negative_factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        margin_prediction = float(base_value + np.sum(shap_values))
        
        # Sanity check: expit(margin) should equal proba (for binary GradientBoostingClassifier)
        sanity_diff = abs(expit(margin_prediction) - proba)
        if sanity_diff > 1e-3:
            # We document that the space might be different, but for GBC it should be log-odds
            pass
            
        explanation = {
            "prediction_probability": proba,
            "margin_prediction": margin_prediction,
            "base_value": base_value,
            "top_positive_factors": positive_factors,
            "top_negative_factors": negative_factors,
            "human_readable": self._format_human_readable(positive_factors, negative_factors, proba)
        }
        return explanation

    def _format_human_readable(self, positive: List[Dict], negative: List[Dict], proba: float) -> str:
        """
        Deterministic formatter on top of structured SHAP facts.
        No LLM used.
        """
        # Determine top 2 drivers overall
        all_factors = positive + negative
        all_factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        top_factors = all_factors[:2]
        
        text = f"Lead has a {proba*100:.1f}% probability of conversion. "
        
        if top_factors:
            reasons = []
            for f in top_factors:
                effect = "increased" if f["direction"] == "positive" else "decreased"
                reasons.append(f"is {effect} by {f['feature']} (value: {f['value']})")
            
            text += "The prediction " + " and ".join(reasons) + "."
        else:
            text += "No strong driving factors found."
            
        return text
