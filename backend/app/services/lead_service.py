from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from app.ml.engine import MLEngine
from app.services.recommendation import RecommendationEngine
from app.schemas.lead import (
    CombinedLeadIntelligenceResponse,
    FactorDetail,
    LeadExplanationResponse,
    LeadRecommendationResponse,
    LeadScoreResponse,
    RankedLeadItem,
    RankedLeadsResponse,
    RuleTrace,
)


class LeadService:
    """
    Lead Service layer.
    Orchestrates the ML Engine, SHAP Explainer, and Recommendation Engine
    to provide clean, typed business responses for API endpoints.
    """

    def __init__(
        self,
        model_path: str = "data/model.joblib",
        features_path: str = "data/model_ready_features.csv",
        raw_leads_path: str = "data/leads.csv",
    ):
        self.model_path = model_path
        self.features_path = features_path
        self.raw_leads_path = raw_leads_path

        # Initialize engines
        self.ml_engine = MLEngine(model_path=model_path)
        self.recommendation_engine = RecommendationEngine()
        self._cached_dataset: Optional[pd.DataFrame] = None
        self._cached_raw_leads: Optional[pd.DataFrame] = None

    def _load_dataset(self) -> pd.DataFrame:
        """
        Loads the model-ready features dataset from disk.
        """
        if self._cached_dataset is None:
            if Path(self.features_path).exists():
                self._cached_dataset = pd.read_csv(self.features_path)
            else:
                self._cached_dataset = pd.DataFrame()
        return self._cached_dataset

    def _load_raw_leads(self) -> pd.DataFrame:
        """
        Loads the raw leads dataset for metadata lookup.
        """
        if self._cached_raw_leads is None:
            if Path(self.raw_leads_path).exists():
                self._cached_raw_leads = pd.read_csv(self.raw_leads_path)
            else:
                self._cached_raw_leads = pd.DataFrame()
        return self._cached_raw_leads

    def score_lead(self, lead_data: Dict[str, Any]) -> LeadScoreResponse:
        """
        Calculates conversion probability and integer lead score using the ML Engine.
        """
        pred = self.ml_engine.predict_lead(lead_data)
        lead_id = lead_data.get("lead_id")

        return LeadScoreResponse(
            lead_id=lead_id,
            conversion_probability=pred["conversion_probability"],
            lead_score=pred["lead_score"],
        )

    def explain_lead(self, lead_data: Dict[str, Any], top_n: int = 5) -> LeadExplanationResponse:
        """
        Generates local SHAP explanation with positive/negative factors and natural language rationale.
        """
        lead_id = lead_data.get("lead_id")
        explanation = self.ml_engine.explain_lead(lead_data, lead_id=lead_id, top_n=top_n)

        return LeadExplanationResponse(
            lead_id=explanation["lead_id"],
            lead_score=explanation["lead_score"],
            conversion_probability=explanation["conversion_probability"],
            base_value=explanation["base_value"],
            positive_factors=[FactorDetail(**f) for f in explanation["positive_factors"]],
            negative_factors=[FactorDetail(**f) for f in explanation["negative_factors"]],
            top_factors=[FactorDetail(**f) for f in explanation["top_factors"]],
            explanation_text=explanation["explanation_text"],
        )

    def recommend_action(self, lead_data: Dict[str, Any]) -> LeadRecommendationResponse:
        """
        Evaluates Next-Best-Action recommendation rules and explicit confidence.
        """
        # If score is not provided, calculate via ML Engine
        lead_score = lead_data.get("lead_score")
        conversion_prob = lead_data.get("conversion_probability")
        if lead_score is None:
            pred = self.ml_engine.predict_lead(lead_data)
            lead_score = pred["lead_score"]
            conversion_prob = pred["conversion_probability"]

        rec = self.recommendation_engine.recommend(
            lead_data=lead_data,
            lead_id=lead_data.get("lead_id"),
            lead_score=lead_score,
            conversion_probability=conversion_prob,
        )

        return LeadRecommendationResponse(
            lead_id=rec["lead_id"],
            lead_score=rec["lead_score"],
            conversion_probability=rec["conversion_probability"],
            recommended_action=rec["recommended_action"],
            recommendation_confidence=rec["recommendation_confidence"],
            confidence_reasons=rec["confidence_reasons"],
            rationale=rec["rationale"],
            rule_trace=RuleTrace(**rec["rule_trace"]),
        )

    def get_lead_intelligence(self, lead_data: Dict[str, Any], top_n: int = 5) -> CombinedLeadIntelligenceResponse:
        """
        Combines Scoring, SHAP Explanation, and Next-Best-Action into a unified intelligence response.
        """
        score_res = self.score_lead(lead_data)

        # Merge calculated score/prob into lead_data for explanation & recommendation
        data_with_score = dict(lead_data)
        data_with_score["lead_score"] = score_res.lead_score
        data_with_score["conversion_probability"] = score_res.conversion_probability

        explanation_res = self.explain_lead(data_with_score, top_n=top_n)
        recommendation_res = self.recommend_action(data_with_score)

        return CombinedLeadIntelligenceResponse(
            lead_id=score_res.lead_id,
            conversion_probability=score_res.conversion_probability,
            lead_score=score_res.lead_score,
            explanation=explanation_res,
            recommendation=recommendation_res,
        )

    def get_lead_by_id(self, lead_id: str) -> Optional[CombinedLeadIntelligenceResponse]:
        """
        Looks up an existing lead from the dataset by ID and returns its combined intelligence.
        """
        df = self._load_dataset()
        if df.empty or "lead_id" not in df.columns:
            return None

        match = df[df["lead_id"] == lead_id]
        if match.empty:
            return None

        record = match.iloc[0].to_dict()
        return self.get_lead_intelligence(record)

    def get_ranked_leads(self, limit: int = 50, offset: int = 0) -> RankedLeadsResponse:
        """
        Returns a paginated list of leads ranked by their ML lead score in descending order.
        """
        df = self._load_dataset()
        raw_df = self._load_raw_leads()

        if df.empty:
            return RankedLeadsResponse(total=0, limit=limit, offset=offset, leads=[])

        # Compute predictions for all leads
        pred_df = self.ml_engine.predict_batch(df)

        # Compute recommendations for all leads
        recs = self.recommendation_engine.recommend_batch(
            pd.concat([df.drop(columns=[c for c in ["lead_score", "conversion_probability"] if c in df.columns]), pred_df[["lead_score", "conversion_probability"]]], axis=1)
        )

        ranked_items: List[RankedLeadItem] = []
        raw_lookup = {}
        if not raw_df.empty and "lead_id" in raw_df.columns:
            raw_lookup = raw_df.set_index("lead_id").to_dict(orient="index")

        for i, row in pred_df.iterrows():
            lid = str(row["lead_id"])
            raw_meta = raw_lookup.get(lid, {})
            rec = recs[i]

            ranked_items.append(
                RankedLeadItem(
                    lead_id=lid,
                    lead_score=int(row["lead_score"]),
                    conversion_probability=float(row["conversion_probability"]),
                    recommended_action=rec["recommended_action"],
                    recommendation_confidence=float(rec["recommendation_confidence"]),
                    opportunity_stage=raw_meta.get("opportunity_stage"),
                    deal_value=float(raw_meta.get("deal_value", 0.0)) if raw_meta.get("deal_value") is not None else None,
                    company_size=raw_meta.get("company_size"),
                    industry=raw_meta.get("industry"),
                )
            )

        # Sort descending by lead score
        ranked_items.sort(key=lambda x: (x.lead_score, x.conversion_probability), reverse=True)

        total_count = len(ranked_items)
        paginated_leads = ranked_items[offset : offset + limit]

        return RankedLeadsResponse(
            total=total_count,
            limit=limit,
            offset=offset,
            leads=paginated_leads,
        )


# Global singleton instance for application route injection
lead_service = LeadService()
