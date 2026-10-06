from typing import List, Optional
import logging
from sqlmodel import Session, select
from app.models.feedback import Feedback
from app.models.lead import Lead
from app.models.recommendation import Recommendation as DBRecommendation
from app.schemas.feedback import FeedbackAcceptInput, FeedbackOverrideInput
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"CALL", "EMAIL", "DEMO", "NURTURE", "REVIEW"}

class FeedbackService:
    def _validate_recommendation_exists(self, lead_id: str, original_action: str, session: Session):
        # 1. Validate lead exists
        lead = session.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
            
        # 2. Validate original recommendation matches exactly
        rec = session.exec(
            select(DBRecommendation).where(DBRecommendation.lead_id == lead_id).order_by(DBRecommendation.timestamp.desc())
        ).first()
        
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original recommendation not found for this lead")
            
        if rec.recommended_action != original_action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Original action mismatch. Current recommendation is {rec.recommended_action}"
            )

    def record_accept(self, lead_id: str, input_data: FeedbackAcceptInput, session: Session) -> Feedback:
        if input_data.original_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid original action. Must be one of {VALID_ACTIONS}")
            
        self._validate_recommendation_exists(lead_id, input_data.original_action, session)
            
        feedback = Feedback(
            lead_id=lead_id,
            original_action=input_data.original_action,
            actor_context=input_data.actor_context,
        )
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        logger.info(f"Override accepted for lead_id={lead_id}, action={input_data.original_action}, actor={input_data.actor_context}")
        return feedback

    def record_override(self, lead_id: str, input_data: FeedbackOverrideInput, session: Session) -> Feedback:
        if input_data.original_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid original action. Must be one of {VALID_ACTIONS}")
        if input_data.override_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid override action. Must be one of {VALID_ACTIONS}")
        if not input_data.reason or not input_data.reason.strip():
            raise HTTPException(status_code=400, detail="Override reason is required")
            
        self._validate_recommendation_exists(lead_id, input_data.original_action, session)
            
        feedback = Feedback(
            lead_id=lead_id,
            original_action=input_data.original_action,
            override_action=input_data.override_action,
            reason=input_data.reason.strip(),
            actor_context=input_data.actor_context,
        )
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        logger.info(f"Override created for lead_id={lead_id}, original={input_data.original_action}, override={input_data.override_action}, actor={input_data.actor_context}")
        return feedback
        
    def get_feedback_for_lead(self, lead_id: str, session: Session) -> List[Feedback]:
        statement = select(Feedback).where(Feedback.lead_id == lead_id).order_by(Feedback.timestamp.desc())
        return list(session.exec(statement).all())
        
    def get_all_feedback(self, session: Session, limit: int = 50, offset: int = 0) -> List[Feedback]:
        statement = select(Feedback).order_by(Feedback.timestamp.desc()).offset(offset).limit(limit)
        return list(session.exec(statement).all())

feedback_service = FeedbackService()
