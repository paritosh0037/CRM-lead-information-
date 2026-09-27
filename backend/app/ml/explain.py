import os
# Ensure numba JIT does not trigger Windows App Control blocks on native DLLs
os.environ["NUMBA_DISABLE_JIT"] = "1"

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
import shap


FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "demo_requested": "Demo Requested",
    "pricing_page_visit": "Pricing Page Visits",
    "email_opened": "Emails Opened",
    "email_clicked": "Email Links Clicked",
    "call_made": "Calls Made",
    "web_visit": "Website Visits",
    "total_web_duration": "Website Duration (Seconds)",
    "total_interactions": "Total Interactions",
    "days_since_last_contact": "Days Since Last Contact",
    "deal_value": "Deal Value ($)",
    "annual_revenue": "Annual Revenue ($)",
    "budget": "Budget ($)",
    "previous_purchase": "Previous Purchase History",
    "industry_Finance": "Industry: Finance",
    "industry_Healthcare": "Industry: Healthcare",
    "industry_Manufacturing": "Industry: Manufacturing",
    "industry_Retail": "Industry: Retail",
    "industry_Technology": "Industry: Technology",
    "company_size_1-50": "Company Size: 1-50",
    "company_size_51-200": "Company Size: 51-200",
    "company_size_201-1000": "Company Size: 201-1000",
    "company_size_1000+": "Company Size: 1000+",
    "lead_source_Event": "Lead Source: Event",
    "lead_source_Organic Search": "Lead Source: Organic Search",
    "lead_source_Outbound": "Lead Source: Outbound",
    "lead_source_Paid Ads": "Lead Source: Paid Ads",
    "lead_source_Referral": "Lead Source: Referral",
    "opportunity_stage_Contacted": "Opportunity Stage: Contacted",
    "opportunity_stage_New": "Opportunity Stage: New",
    "opportunity_stage_Proposal": "Opportunity Stage: Proposal",
    "opportunity_stage_Qualified": "Opportunity Stage: Qualified",
}


def get_display_name(feature_name: str) -> str:
    """
    Maps an engineered feature name to a clean, human-readable CRM business term.
    """
    if feature_name in FEATURE_DISPLAY_NAMES:
        return FEATURE_DISPLAY_NAMES[feature_name]
    return feature_name.replace("_", " ").title()


def generate_natural_language_explanation(
    positive_factors: List[Dict[str, Any]],
    negative_factors: List[Dict[str, Any]],
    lead_score: Optional[int] = None,
) -> str:
    """
    Generates a concise, deterministic natural-language explanation derived strictly
    from the positive and negative SHAP contribution factors.
    """
    pos_phrases = []
    for factor in positive_factors[:3]:
        name = factor["display_name"].lower()
        pos_phrases.append(name)

    neg_phrases = []
    for factor in negative_factors[:2]:
        name = factor["display_name"].lower()
        neg_phrases.append(name)

    # Build rationale
    score_qualifier = "Strong conversion potential"
    if lead_score is not None:
        if lead_score >= 80:
            score_qualifier = "High conversion potential"
        elif lead_score >= 50:
            score_qualifier = "Moderate conversion potential"
        else:
            score_qualifier = "Lower conversion potential"

    if pos_phrases and neg_phrases:
        pos_text = ", ".join(pos_phrases[:-1]) + (" and " + pos_phrases[-1] if len(pos_phrases) > 1 else pos_phrases[0])
        neg_text = ", ".join(neg_phrases[:-1]) + (" and " + neg_phrases[-1] if len(neg_phrases) > 1 else neg_phrases[0])
        return (
            f"{score_qualifier} driven positively by {pos_text}. "
            f"Conversely, {neg_text} reduced the score."
        )
    elif pos_phrases:
        pos_text = ", ".join(pos_phrases[:-1]) + (" and " + pos_phrases[-1] if len(pos_phrases) > 1 else pos_phrases[0])
        return f"{score_qualifier} driven primarily by {pos_text}."
    elif neg_phrases:
        neg_text = ", ".join(neg_phrases[:-1]) + (" and " + neg_phrases[-1] if len(neg_phrases) > 1 else neg_phrases[0])
        return f"{score_qualifier} constrained primarily by {neg_text}."
    else:
        return f"{score_qualifier} aligned with baseline pipeline behavior."


class SHAPExplainer:
    """
    SHAP-based Lead Explainer.

    Computes local feature-level contributions (Tree SHAP) for individual leads
    and global feature importance across evaluation datasets.
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        model_path: Optional[str] = "data/model.joblib",
        feature_names: Optional[List[str]] = None,
    ):
        self.model = model
        self.feature_names = feature_names or []
        self.explainer = None

        if self.model is None and model_path and Path(model_path).exists():
            artifact = joblib.load(model_path)
            if isinstance(artifact, dict) and "model" in artifact:
                self.model = artifact["model"]
                self.feature_names = artifact.get("feature_names", [])
            else:
                self.model = artifact

        if self.model is not None:
            self._init_explainer()

    def _init_explainer(self):
        """
        Initializes the SHAP TreeExplainer.
        """
        self.explainer = shap.TreeExplainer(self.model)

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans and aligns input features to match model expectations.
        """
        df = X.copy()
        for col in ["lead_id", "converted"]:
            if col in df.columns:
                df = df.drop(columns=[col])

        sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
        for attr in sensitive_attrs:
            if attr in df.columns:
                df = df.drop(columns=[attr])

        if self.feature_names:
            for feat in self.feature_names:
                if feat not in df.columns:
                    df[feat] = 0
            df = df[self.feature_names]

        return df

    def explain_lead(
        self,
        lead_features: pd.DataFrame | Dict[str, Any],
        lead_id: Optional[str] = None,
        lead_score: Optional[int] = None,
        conversion_probability: Optional[float] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """
        Explains an individual lead's prediction using Tree SHAP.
        Returns positive factors, negative factors, top factors, and natural-language rationale.
        """
        if self.explainer is None:
            raise ValueError("SHAP Explainer has not been initialized with a model.")

        if isinstance(lead_features, dict):
            extracted_id = lead_features.get("lead_id", lead_id)
            extracted_score = lead_features.get("lead_score", lead_score)
            extracted_prob = lead_features.get("conversion_probability", conversion_probability)
            df = pd.DataFrame([lead_features])
        else:
            extracted_id = lead_features["lead_id"].iloc[0] if "lead_id" in lead_features.columns else lead_id
            extracted_score = lead_features["lead_score"].iloc[0] if "lead_score" in lead_features.columns else lead_score
            extracted_prob = (
                lead_features["conversion_probability"].iloc[0]
                if "conversion_probability" in lead_features.columns
                else conversion_probability
            )
            df = lead_features.iloc[[0]].copy()

        df_prep = self._prepare_features(df)
        shap_values = self.explainer.shap_values(df_prep)

        # GradientBoostingClassifier shap_values shape: (1, n_features) or (n_features,)
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif len(shap_values.shape) == 2:
            sv = shap_values[0]
        else:
            sv = shap_values

        base_val = float(
            self.explainer.expected_value[0]
            if isinstance(self.explainer.expected_value, (list, np.ndarray))
            else self.explainer.expected_value
        )

        factors = []
        for feat_name, impact in zip(df_prep.columns, sv):
            raw_val = df_prep[feat_name].iloc[0]
            # Convert numpy types to standard python types for JSON serialization
            if isinstance(raw_val, (np.integer, np.floating)):
                raw_val = raw_val.item()

            factors.append(
                {
                    "feature": feat_name,
                    "display_name": get_display_name(feat_name),
                    "impact": round(float(impact), 4),
                    "raw_value": raw_val,
                }
            )

        # Positive contributing factors (impact > 0), sorted descending
        positive_factors = [f for f in factors if f["impact"] > 0]
        positive_factors.sort(key=lambda x: x["impact"], reverse=True)

        # Negative contributing factors (impact < 0), sorted ascending (strongest negative first)
        negative_factors = [f for f in factors if f["impact"] < 0]
        negative_factors.sort(key=lambda x: x["impact"])

        # Combined top factors sorted by absolute magnitude
        top_factors = sorted(factors, key=lambda x: abs(x["impact"]), reverse=True)[:top_n]

        # Natural language summary
        explanation_text = generate_natural_language_explanation(
            positive_factors, negative_factors, lead_score=extracted_score
        )

        return {
            "lead_id": extracted_id,
            "lead_score": extracted_score,
            "conversion_probability": extracted_prob,
            "base_value": round(base_val, 4),
            "positive_factors": positive_factors[:top_n],
            "negative_factors": negative_factors[:top_n],
            "top_factors": top_factors,
            "explanation_text": explanation_text,
        }

    def get_global_feature_importance(
        self, X: pd.DataFrame, top_n: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Computes global feature importance based on mean absolute SHAP values.
        """
        if self.explainer is None:
            raise ValueError("SHAP Explainer has not been initialized.")

        X_prep = self._prepare_features(X)
        shap_values = self.explainer.shap_values(X_prep)

        if isinstance(shap_values, list):
            sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            sv = shap_values

        mean_abs_shap = np.mean(np.abs(sv), axis=0)

        importance_list = []
        for feat, imp in zip(X_prep.columns, mean_abs_shap):
            importance_list.append(
                {
                    "feature": feat,
                    "display_name": get_display_name(feat),
                    "mean_abs_shap": round(float(imp), 4),
                }
            )

        importance_list.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        return importance_list[:top_n]

    def save_global_importance(
        self, X: pd.DataFrame, output_path: str = "data/shap_global_importance.json", top_n: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Computes and persists global SHAP feature importance to a JSON artifact.
        """
        importance = self.get_global_feature_importance(X, top_n=top_n)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w") as f:
            json.dump(importance, f, indent=2)
        return importance


if __name__ == "__main__":
    df = pd.read_csv("f:/pending project/CRM project/backend/data/model_ready_features.csv")
    explainer = SHAPExplainer(model_path="f:/pending project/CRM project/backend/data/model.joblib")
    
    # Explain first lead
    first_lead = df.iloc[0].to_dict()
    explanation = explainer.explain_lead(first_lead, lead_id=first_lead.get("lead_id"))
    print("Example Lead Explanation:")
    print(json.dumps(explanation, indent=2))
    
    # Save global importance
    importance = explainer.save_global_importance(
        df.drop(columns=["lead_id", "converted"]),
        output_path="f:/pending project/CRM project/backend/data/shap_global_importance.json"
    )
    print(f"\nTop 5 Global Features by Mean |SHAP|: {[f['display_name'] for f in importance[:5]]}")
