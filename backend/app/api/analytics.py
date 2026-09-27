from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from pydantic import BaseModel
from typing import Dict, Any

from app.core.database import get_session
from app.models.lead import Lead

router = APIRouter(prefix="/analytics", tags=["Analytics"])

class AnalyticsResponse(BaseModel):
    total_leads: int
    high_priority_leads: int
    pipeline_value: float
    average_lead_score: float
    score_distribution: Dict[str, int]
    score_by_opportunity_stage: Dict[str, float]
    action_distribution: Dict[str, int]

@router.get("", response_model=AnalyticsResponse, summary="Get Dashboard Analytics")
def get_analytics(session: Session = Depends(get_session)) -> AnalyticsResponse:
    try:
        total_leads = session.exec(select(func.count(Lead.id))).one()
        
        # High Priority: score >= 75
        high_priority = session.exec(
            select(func.count(Lead.id)).where(Lead.lead_score >= 75)
        ).one()
        
        # Pipeline Value (sum of deal_value)
        pipeline_val = session.exec(
            select(func.sum(Lead.deal_value))
        ).one()
        pipeline_value = float(pipeline_val) if pipeline_val else 0.0
        
        # Average Lead Score
        avg_score = session.exec(
            select(func.avg(Lead.lead_score))
        ).one()
        average_lead_score = float(avg_score) if avg_score else 0.0
        
        # Score distribution (bins: 0-25, 26-50, 51-75, 76-100)
        # We can do this in Python since the total count is ~5000 leads (small enough to fetch or group)
        leads = session.exec(select(Lead)).all()
        
        dist = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
        stage_scores = {}
        stage_counts = {}
        action_dist = {}
        
        for lead in leads:
            score = lead.lead_score or 0
            if score <= 25: dist["0-25"] += 1
            elif score <= 50: dist["26-50"] += 1
            elif score <= 75: dist["51-75"] += 1
            else: dist["76-100"] += 1
            
            stage = lead.opportunity_stage or "Unknown"
            if stage not in stage_scores:
                stage_scores[stage] = 0.0
                stage_counts[stage] = 0
            stage_scores[stage] += score
            stage_counts[stage] += 1
            
            action = lead.recommended_action or "NONE"
            action_dist[action] = action_dist.get(action, 0) + 1
            
        score_by_stage = {
            stage: round(stage_scores[stage] / stage_counts[stage], 2)
            for stage in stage_scores
        }

        return AnalyticsResponse(
            total_leads=total_leads,
            high_priority_leads=high_priority,
            pipeline_value=pipeline_value,
            average_lead_score=round(average_lead_score, 2),
            score_distribution=dist,
            score_by_opportunity_stage=score_by_stage,
            action_distribution=action_dist
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
