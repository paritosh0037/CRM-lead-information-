from typing import List, Optional
from sqlmodel import Session, select
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackAcceptInput, FeedbackOverrideInput
from fastapi import HTTPException, status

VALID_ACTIONS = {"CALL", "EMAIL", "DEMO", "NURTURE", "REVIEW"}

class FeedbackService:
    def record_accept(self, lead_id: str, input_data: FeedbackAcceptInput, session: Session) -> Feedback:
        if input_data.original_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid original action. Must be one of {VALID_ACTIONS}")
            
        feedback = Feedback(
            lead_id=lead_id,
            original_action=input_data.original_action,
        )
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        return feedback

    def record_override(self, lead_id: str, input_data: FeedbackOverrideInput, session: Session) -> Feedback:
        if input_data.original_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid original action. Must be one of {VALID_ACTIONS}")
        if input_data.override_action not in VALID_ACTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid override action. Must be one of {VALID_ACTIONS}")
        if not input_data.reason or not input_data.reason.strip():
            raise HTTPException(status_code=400, detail="Override reason is required")
            
        feedback = Feedback(
            lead_id=lead_id,
            original_action=input_data.original_action,
            override_action=input_data.override_action,
            reason=input_data.reason.strip(),
        )
        session.add(feedback)
        session.commit()
        session.refresh(feedback)
        return feedback
        
    def get_feedback_for_lead(self, lead_id: str, session: Session) -> List[Feedback]:
        statement = select(Feedback).where(Feedback.lead_id == lead_id).order_by(Feedback.timestamp.desc())
        return list(session.exec(statement).all())
        
    def get_all_feedback(self, session: Session, limit: int = 50, offset: int = 0) -> List[Feedback]:
        statement = select(Feedback).order_by(Feedback.timestamp.desc()).offset(offset).limit(limit)
        return list(session.exec(statement).all())

feedback_service = FeedbackService()
