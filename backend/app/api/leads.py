from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.lead import (
    CombinedLeadIntelligenceResponse,
    LeadExplanationResponse,
    LeadFeaturesInput,
    LeadRecommendationResponse,
    LeadScoreResponse,
    RankedLeadsResponse,
)
from app.services.lead_service import lead_service

router = APIRouter(prefix="/leads", tags=["Leads & Intelligence"])


@router.post(
    "/score",
    response_model=LeadScoreResponse,
    summary="Predict Lead Conversion Probability & Score",
    description="Consumes lead features and returns predicted conversion probability and 0-100 lead score from the ML Engine.",
)
def score_lead(lead_input: LeadFeaturesInput) -> LeadScoreResponse:
    try:
        return lead_service.score_lead(lead_input.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead scoring failed: {str(e)}",
        )


@router.post(
    "/explain",
    response_model=LeadExplanationResponse,
    summary="Explain Lead Score via SHAP",
    description="Computes exact Tree SHAP positive/negative contributing factors and natural language rationale for a lead.",
)
def explain_lead(
    lead_input: LeadFeaturesInput,
    top_n: int = Query(5, ge=1, le=20, description="Number of top factors to return"),
) -> LeadExplanationResponse:
    try:
        return lead_service.explain_lead(lead_input.model_dump(), top_n=top_n)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead explanation failed: {str(e)}",
        )


@router.post(
    "/recommend",
    response_model=LeadRecommendationResponse,
    summary="Get Next-Best-Action Recommendation",
    description="Evaluates deterministic score-band rules and CRM behavioral signals to recommend sales actions (CALL, EMAIL, DEMO, NURTURE, REVIEW).",
)
def recommend_action(lead_input: LeadFeaturesInput) -> LeadRecommendationResponse:
    try:
        return lead_service.recommend_action(lead_input.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation calculation failed: {str(e)}",
        )


@router.post(
    "/intelligence",
    response_model=CombinedLeadIntelligenceResponse,
    summary="Combined Lead Intelligence (Scoring + SHAP + Recommendation)",
    description="Generates end-to-end intelligence for an input lead record in a unified response.",
)
def get_lead_intelligence(
    lead_input: LeadFeaturesInput,
    top_n: int = Query(5, ge=1, le=20, description="Number of top factors to return"),
) -> CombinedLeadIntelligenceResponse:
    try:
        return lead_service.get_lead_intelligence(lead_input.model_dump(), top_n=top_n)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead intelligence processing failed: {str(e)}",
        )


@router.get(
    "/ranked",
    response_model=RankedLeadsResponse,
    summary="Get Prioritized & Ranked Leads",
    description="Returns stored CRM leads ranked by ML lead score in descending order.",
)
def get_ranked_leads(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of leads to return"),
    offset: int = Query(0, ge=0, description="Number of leads to skip"),
) -> RankedLeadsResponse:
    try:
        return lead_service.get_ranked_leads(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ranked leads: {str(e)}",
        )


@router.get(
    "",
    response_model=RankedLeadsResponse,
    summary="List Leads",
    description="Lists all CRM leads with current scoring and recommendations.",
)
def list_leads(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> RankedLeadsResponse:
    return get_ranked_leads(limit=limit, offset=offset)


@router.get(
    "/{lead_id}",
    response_model=CombinedLeadIntelligenceResponse,
    summary="Get Single Lead Intelligence by ID",
    description="Fetches stored CRM lead data by ID and returns its combined scoring, SHAP explanation, and Next-Best-Action recommendation.",
)
def get_lead_by_id(lead_id: str) -> CombinedLeadIntelligenceResponse:
    intel = lead_service.get_lead_by_id(lead_id)
    if intel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID '{lead_id}' not found.",
        )
    return intel
