from typing import List
from fastapi import APIRouter, Depends, Query, Path
from sqlmodel import Session
from app.core.database import get_session
from app.schemas.feedback import FeedbackAcceptInput, FeedbackOverrideInput, FeedbackResponse
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/{lead_id}/accept", response_model=FeedbackResponse, summary="Accept Recommendation")
def accept_recommendation(
    lead_id: str = Path(..., description="The lead ID"),
    input_data: FeedbackAcceptInput = None,
    session: Session = Depends(get_session)
):
    return feedback_service.record_accept(lead_id, input_data, session)

@router.post("/{lead_id}/override", response_model=FeedbackResponse, summary="Override Recommendation")
def override_recommendation(
    lead_id: str = Path(..., description="The lead ID"),
    input_data: FeedbackOverrideInput = None,
    session: Session = Depends(get_session)
):
    return feedback_service.record_override(lead_id, input_data, session)

@router.get("/{lead_id}", response_model=List[FeedbackResponse], summary="Get Feedback for Lead")
def get_feedback_for_lead(
    lead_id: str = Path(..., description="The lead ID"),
    session: Session = Depends(get_session)
):
    return feedback_service.get_feedback_for_lead(lead_id, session)
    
@router.get("", response_model=List[FeedbackResponse], summary="List All Feedback")
def list_all_feedback(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)
):
    return feedback_service.get_all_feedback(session, limit, offset)
