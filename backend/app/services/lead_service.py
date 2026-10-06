from typing import Any, Dict, List, Optional
import pandas as pd
from sqlmodel import Session, select
from fastapi import Depends
import datetime
import logging

logger = logging.getLogger(__name__)

from app.core.database import engine, get_session
from app.models.lead import Lead
from app.models.interaction import Interaction
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation as DBRecommendation
from app.ml.feature_engineering import engineer_features

from app.ml.model import MLModel
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
    Orchestrates the MLModel (prediction/explainability) and Recommendation Engine
    to provide clean, typed business responses for API endpoints.
    """

    def __init__(
        self,
        model_path: str = "data/model.joblib",
    ):
        self.model_path = model_path

        # Initialize engines
        self.ml_model = MLModel(artifact_path=model_path)
        self.recommendation_engine = RecommendationEngine()

    def _get_db_session(self) -> Session:
        return Session(engine)

    def _build_features_from_db(self, session: Session, lead_id: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieves leads and interactions from the DB and engineers features.
        If lead_id is provided, fetches only that lead. Otherwise fetches all.
        """
        if lead_id:
            db_leads = session.exec(select(Lead).where(Lead.lead_id == lead_id)).all()
            if not db_leads:
                return pd.DataFrame()
            db_interactions = session.exec(select(Interaction).where(Interaction.lead_id == lead_id)).all()
        else:
            db_leads = session.exec(select(Lead)).all()
            db_interactions = session.exec(select(Interaction)).all()

        if not db_leads:
            return pd.DataFrame()

        # Convert to DataFrames
        leads_df = pd.DataFrame([lead.model_dump() for lead in db_leads])
        interactions_df = pd.DataFrame([inter.model_dump() for inter in db_interactions])

        # Engineer features using the ML pipeline module
        features, _, _ = engineer_features(leads_df, interactions_df)
        
        # Add lead_id back to features dataframe for indexing/tracking
        features["lead_id"] = leads_df["lead_id"].values
        return features

    def score_lead(self, lead_data: Dict[str, Any]) -> LeadScoreResponse:
        """
        Calculates conversion probability and integer lead score using the MLModel.
        """
        df = pd.DataFrame([lead_data])
        raw_prob = self.ml_model.predict_probability(df)
        
        # In case it returns an array for a single row (depends on input length), extract it
        if isinstance(raw_prob, (list, pd.Series, pd.Index)) or hasattr(raw_prob, "__len__"):
            prob = float(raw_prob[0])
        else:
            prob = float(raw_prob)
            
        prob = round(prob, 4)
        lead_score = int(round(prob * 100))
        lead_id = lead_data.get("lead_id")

        return LeadScoreResponse(
            lead_id=lead_id,
            conversion_probability=prob,
            lead_score=lead_score,
        )

    def explain_lead(self, lead_data: Dict[str, Any], top_n: int = 5) -> LeadExplanationResponse:
        """
        Generates local SHAP explanation with positive/negative factors and natural language rationale.
        """
        df = pd.DataFrame([lead_data])
        explanation = self.ml_model.explain(df)

        lead_id = lead_data.get("lead_id")
        
        # Optionally limit factors to top_n
        pos_factors = explanation["top_positive_factors"][:top_n]
        neg_factors = explanation["top_negative_factors"][:top_n]
        top_factors = (explanation["top_positive_factors"] + explanation["top_negative_factors"])
        top_factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        top_factors = top_factors[:top_n]

        # Convert to FactorDetail mapping structure
        def _to_factor_detail(f):
            return FactorDetail(
                feature=f["feature"],
                display_name=f["feature"].replace("_", " ").title(),
                impact=f["shap_value"],
                raw_value=f["value"]
            )

        return LeadExplanationResponse(
            lead_id=lead_id,
            lead_score=lead_data.get("lead_score"),
            conversion_probability=lead_data.get("conversion_probability"),
            base_value=explanation["base_value"],
            positive_factors=[_to_factor_detail(f) for f in pos_factors],
            negative_factors=[_to_factor_detail(f) for f in neg_factors],
            top_factors=[_to_factor_detail(f) for f in top_factors],
            explanation_text=explanation["human_readable"],
        )

    def recommend_action(self, lead_data: Dict[str, Any]) -> LeadRecommendationResponse:
        """
        Evaluates Next-Best-Action recommendation rules and explicit confidence.
        """
        # If score is not provided, calculate via MLModel
        lead_score = lead_data.get("lead_score")
        conversion_prob = lead_data.get("conversion_probability")
        if lead_score is None:
            score_res = self.score_lead(lead_data)
            lead_score = score_res.lead_score
            conversion_prob = score_res.conversion_probability

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
        Persists decision traceability in the database.
        """
        score_res = self.score_lead(lead_data)

        # Merge calculated score/prob into lead_data for explanation & recommendation
        data_with_score = dict(lead_data)
        data_with_score["lead_score"] = score_res.lead_score
        data_with_score["conversion_probability"] = score_res.conversion_probability

        explanation_res = self.explain_lead(data_with_score, top_n=top_n)
        recommendation_res = self.recommend_action(data_with_score)

        response = CombinedLeadIntelligenceResponse(
            lead_id=score_res.lead_id,
            conversion_probability=score_res.conversion_probability,
            lead_score=score_res.lead_score,
            explanation=explanation_res,
            recommendation=recommendation_res,
        )
        
        self._persist_decision_trace(response)
        
        return response

    def _persist_decision_trace(self, decision: CombinedLeadIntelligenceResponse):
        """Persists the ML score and recommendation state into database."""
        if not decision.lead_id:
            logger.warning("Attempted to persist decision without lead_id.")
            return
            
        model_version = self.ml_model._metadata.get("model_version", "unknown") if self.ml_model._metadata else "unknown"
            
        with self._get_db_session() as session:
            # Upsert Prediction
            pred_record = session.exec(select(Prediction).where(Prediction.lead_id == decision.lead_id)).first()
            if not pred_record:
                pred_record = Prediction(lead_id=decision.lead_id)
                session.add(pred_record)
            
            pred_record.conversion_probability = decision.conversion_probability
            pred_record.lead_score = decision.lead_score
            pred_record.model_version = model_version
            pred_record.predicted_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Upsert Recommendation
            rec_record = session.exec(select(DBRecommendation).where(DBRecommendation.lead_id == decision.lead_id)).first()
            if not rec_record:
                rec_record = DBRecommendation(lead_id=decision.lead_id)
                session.add(rec_record)
                
            rec_record.recommended_action = decision.recommendation.recommended_action
            rec_record.confidence_score = decision.recommendation.recommendation_confidence
            rec_record.rationale = decision.recommendation.rationale
            rec_record.recommended_at = datetime.datetime.now(datetime.timezone.utc)
            
            session.commit()
            
        logger.info(f"Inference executed for lead_id={decision.lead_id}, model_version={model_version}")
        logger.info(f"Recommendation generated for lead_id={decision.lead_id}, action={decision.recommendation.recommended_action}")

    def get_lead_by_id(self, lead_id: str) -> Optional[CombinedLeadIntelligenceResponse]:
        """
        Looks up an existing lead from the DB by ID and returns its combined intelligence.
        """
        with self._get_db_session() as session:
            db_lead = session.get(Lead, lead_id)
            if not db_lead:
                return None

            # Get engineered features for just this lead
            features_df = self._build_features_from_db(session, lead_id=lead_id)
            if features_df.empty:
                return None
                
            record = features_df.iloc[0].to_dict()
            
            # Incorporate raw CRM data not kept in the feature matrix
            record["opportunity_stage"] = db_lead.opportunity_stage
            record["deal_value"] = db_lead.deal_value
            record["company_size"] = db_lead.company_size
            record["industry"] = db_lead.industry

        return self.get_lead_intelligence(record)

    def get_lead_interactions(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Fetches interaction history for a given lead directly from the database.
        Returns them sorted by timestamp descending.
        """
        with self._get_db_session() as session:
            db_interactions = session.exec(
                select(Interaction).where(Interaction.lead_id == lead_id).order_by(Interaction.timestamp.desc())
            ).all()
            return [inter.model_dump() for inter in db_interactions]

    def get_ranked_leads(self, limit: int = 50, offset: int = 0) -> RankedLeadsResponse:
        """
        Returns a paginated list of leads ranked by their ML lead score in descending order.
        """
        with self._get_db_session() as session:
            # Build features from DB for all leads
            features_df = self._build_features_from_db(session)
            if features_df.empty:
                return RankedLeadsResponse(total=0, limit=limit, offset=offset, leads=[])

            # Raw leads for metadata
            db_leads = session.exec(select(Lead)).all()
            raw_lookup = {str(lead.lead_id): lead for lead in db_leads}

        # Predict batch
        probas = self.ml_model.predict_probability(features_df)
        if isinstance(probas, float):
            probas = [probas]
            
        pred_df = pd.DataFrame({
            "lead_id": features_df["lead_id"] if "lead_id" in features_df.columns else range(len(probas)),
            "conversion_probability": probas
        })
        pred_df["lead_score"] = (pred_df["conversion_probability"] * 100).round().astype(int)

        # Compute recommendations for all leads
        features_for_recs = features_df.drop(columns=[c for c in ["lead_score", "conversion_probability"] if c in features_df.columns], errors='ignore')
        combined_for_recs = pd.concat([features_for_recs, pred_df[["lead_score", "conversion_probability"]]], axis=1)
        recs = self.recommendation_engine.recommend_batch(combined_for_recs)

        ranked_items: List[RankedLeadItem] = []

        for i, row in pred_df.iterrows():
            lid = str(row["lead_id"])
            raw_meta = raw_lookup.get(lid)
            rec = recs[i]
            
            # Extract raw values or fallback to 0
            deal_val = float(raw_meta.deal_value) if raw_meta and raw_meta.deal_value is not None else 0.0

            ranked_items.append(
                RankedLeadItem(
                    lead_id=lid,
                    lead_score=int(row["lead_score"]),
                    conversion_probability=float(row["conversion_probability"]),
                    recommended_action=rec["recommended_action"],
                    recommendation_confidence=float(rec["recommendation_confidence"]),
                    opportunity_stage=raw_meta.opportunity_stage if raw_meta else None,
                    deal_value=deal_val,
                    company_size=raw_meta.company_size if raw_meta else None,
                    industry=raw_meta.industry if raw_meta else None,
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
