from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

from app.ml.explain import SHAPExplainer


class MLEngine:
    """
    ML Engine for Lead Scoring, Conversion Prediction, and SHAP Explainability.

    Encapsulates loading the trained ML model artifact, generating conversion
    probabilities, computing 0-100 integer lead scores, validating input features,
    and explaining predictions.
    """

    def __init__(self, model_path: Optional[str] = "data/model.joblib"):
        self.model = None
        self.model_name = None
        self.feature_names: List[str] = []
        self.explainer: Optional[SHAPExplainer] = None
        self.model_path = model_path
        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def load_model(self, model_path: str):
        """
        Loads the trained model artifact from disk using joblib and initializes the SHAP explainer.
        """
        self.model_path = model_path
        artifact = joblib.load(model_path)
        if isinstance(artifact, dict) and "model" in artifact:
            self.model = artifact["model"]
            self.model_name = artifact.get("model_name", "TrainedModel")
            self.feature_names = artifact.get("feature_names", [])
        else:
            self.model = artifact
            self.model_name = "TrainedModel"

        # Initialize SHAP explainer
        self.explainer = SHAPExplainer(
            model=self.model, feature_names=self.feature_names
        )

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Validates feature columns against model requirements, ensuring target and
        sensitive attributes are absent.
        """
        df = X.copy()
        # Remove metadata / target columns if present
        for col in ["lead_id", "converted"]:
            if col in df.columns:
                df = df.drop(columns=[col])

        # Remove prohibited sensitive attributes if present
        sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
        for attr in sensitive_attrs:
            if attr in df.columns:
                df = df.drop(columns=[attr])

        # If feature names are known, align columns
        if self.feature_names:
            for feat in self.feature_names:
                if feat not in df.columns:
                    df[feat] = 0
            df = df[self.feature_names]

        return df

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict conversion probabilities for input feature DataFrame.
        Returns a 1D numpy array of probabilities bounded between 0.0 and 1.0.
        """
        if self.model is None:
            raise ValueError("Model has not been loaded. Call load_model() first.")

        X_prep = self._prepare_features(X)
        proba = self.model.predict_proba(X_prep)[:, 1]
        return np.clip(proba, 0.0, 1.0)

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary conversion outcome based on threshold.
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Calculates Lead Score = Conversion Probability * 100 on [0, 100] integer scale.
        """
        proba = self.predict_proba(X)
        return np.round(proba * 100).astype(int)

    def predict_lead(self, lead_record: Dict[str, Any] | pd.DataFrame) -> Dict[str, Any]:
        """
        Generates structured score and conversion probability for a single lead.
        """
        if isinstance(lead_record, dict):
            df = pd.DataFrame([lead_record])
        else:
            df = lead_record

        raw_proba = float(self.predict_proba(df)[0])
        proba = round(raw_proba, 4)
        lead_score = int(round(proba * 100))

        return {
            "conversion_probability": proba,
            "lead_score": lead_score,
        }

    def explain_lead(
        self,
        lead_record: Dict[str, Any] | pd.DataFrame,
        lead_id: Optional[str] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive SHAP explanation for a lead along with its prediction score.
        """
        pred = self.predict_lead(lead_record)
        if self.explainer is None:
            raise ValueError("Explainer has not been initialized.")

        explanation = self.explainer.explain_lead(
            lead_features=lead_record,
            lead_id=lead_id,
            lead_score=pred["lead_score"],
            conversion_probability=pred["conversion_probability"],
            top_n=top_n,
        )
        return explanation

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates predictions for a batch of leads, returning a DataFrame with lead_id,
        conversion_probability, lead_score, and actual converted label if present.
        """
        lead_ids = df["lead_id"].values if "lead_id" in df.columns else np.arange(len(df))
        raw_proba = self.predict_proba(df)
        proba = np.round(raw_proba, 4)
        scores = np.round(proba * 100).astype(int)

        result = pd.DataFrame(
            {
                "lead_id": lead_ids,
                "conversion_probability": proba,
                "lead_score": scores,
            }
        )

        if "converted" in df.columns:
            result["converted"] = df["converted"].values

        return result
