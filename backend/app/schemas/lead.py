from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class LeadFeaturesInput(BaseModel):
    """
    Input schema for lead features used in scoring, explainability, and recommendation.
    """
    model_config = ConfigDict(extra="allow")

    lead_id: Optional[str] = Field(None, description="Unique lead identifier")
    annual_revenue: Optional[float] = Field(0.0, description="Annual revenue in dollars")
    budget: Optional[float] = Field(0.0, description="Lead budget in dollars")
    deal_value: Optional[float] = Field(0.0, description="Deal value in dollars")
    previous_purchase: Optional[int] = Field(0, description="Previous purchase flag (0 or 1)")
    days_since_last_contact: Optional[int] = Field(30, description="Days since last contact")
    email_opened: Optional[int] = Field(0, description="Number of emails opened")
    email_clicked: Optional[int] = Field(0, description="Number of email links clicked")
    call_made: Optional[int] = Field(0, description="Number of calls made")
    web_visit: Optional[int] = Field(0, description="Number of website visits")
    pricing_page_visit: Optional[int] = Field(0, description="Number of pricing page visits")
    demo_requested: Optional[int] = Field(0, description="Number of demo requests")
    total_web_duration: Optional[int] = Field(0, description="Total website duration in seconds")
    total_interactions: Optional[int] = Field(0, description="Total customer interactions")
    industry: Optional[str] = Field(None, description="Company industry sector")
    company_size: Optional[str] = Field(None, description="Company size bucket")
    lead_source: Optional[str] = Field(None, description="Marketing source channel")
    opportunity_stage: Optional[str] = Field(None, description="Current CRM opportunity stage")


class LeadScoreResponse(BaseModel):
    """
    Response schema for ML lead scoring.
    """
    lead_id: Optional[str] = None
    conversion_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted conversion probability")
    lead_score: int = Field(..., ge=0, le=100, description="Integer lead score from 0 to 100")


class FactorDetail(BaseModel):
    """
    Contributing factor detail from SHAP analysis.
    """
    feature: str = Field(..., description="Raw feature name")
    display_name: str = Field(..., description="Human-readable feature name")
    impact: float = Field(..., description="SHAP impact on log-odds / prediction")
    raw_value: Any = Field(None, description="Raw feature value for this lead")


class LeadExplanationResponse(BaseModel):
    """
    Response schema for SHAP-based feature explanations.
    """
    lead_id: Optional[str] = None
    lead_score: Optional[int] = None
    conversion_probability: Optional[float] = None
    base_value: float = Field(..., description="SHAP explainer base reference value")
    positive_factors: List[FactorDetail] = Field(default_factory=list, description="Top positive factors")
    negative_factors: List[FactorDetail] = Field(default_factory=list, description="Top negative factors")
    top_factors: List[FactorDetail] = Field(default_factory=list, description="Top overall factors")
    explanation_text: str = Field(..., description="Natural language explanation of score drivers")


class RuleTrace(BaseModel):
    """
    Trace of the rule evaluated by the Next-Best-Action engine.
    """
    score_band: str
    trigger: str
    action: str


class LeadRecommendationResponse(BaseModel):
    """
    Response schema for Next-Best-Action recommendations.
    """
    lead_id: Optional[str] = None
    lead_score: int = Field(..., ge=0, le=100)
    conversion_probability: Optional[float] = None
    recommended_action: str = Field(..., description="Recommended sales action: CALL, EMAIL, DEMO, NURTURE, REVIEW")
    recommendation_confidence: float = Field(..., ge=0.0, le=1.0, description="Explicit rule confidence")
    confidence_reasons: List[str] = Field(default_factory=list, description="Reasons for confidence value")
    rationale: str = Field(..., description="Transparent business rationale for the action")
    rule_trace: RuleTrace = Field(..., description="Rule evaluation trace")


class CombinedLeadIntelligenceResponse(BaseModel):
    """
    Comprehensive lead intelligence combining Scoring, SHAP Explanation, and Next-Best-Action.
    """
    lead_id: Optional[str] = None
    conversion_probability: float
    lead_score: int
    explanation: LeadExplanationResponse
    recommendation: LeadRecommendationResponse


class RankedLeadItem(BaseModel):
    """
    Individual lead summary item in the ranked leads listing.
    """
    lead_id: str
    lead_score: int
    conversion_probability: float
    recommended_action: str
    recommendation_confidence: float
    opportunity_stage: Optional[str] = None
    deal_value: Optional[float] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None


class RankedLeadsResponse(BaseModel):
    """
    Paginated list of prioritized and ranked CRM leads.
    """
    total: int
    limit: int
    offset: int
    leads: List[RankedLeadItem]
