from typing import Optional
from sqlmodel import SQLModel, Field

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, unique=True, description="Unique lead identifier")
    
    # CRM Features
    annual_revenue: Optional[float] = 0.0
    budget: Optional[float] = 0.0
    deal_value: Optional[float] = 0.0
    previous_purchase: Optional[int] = 0
    days_since_last_contact: Optional[int] = 30
    email_opened: Optional[int] = 0
    email_clicked: Optional[int] = 0
    call_made: Optional[int] = 0
    web_visit: Optional[int] = 0
    pricing_page_visit: Optional[int] = 0
    demo_requested: Optional[int] = 0
    total_web_duration: Optional[int] = 0
    total_interactions: Optional[int] = 0
    industry: Optional[str] = None
    company_size: Optional[str] = None
    lead_source: Optional[str] = None
    opportunity_stage: Optional[str] = None
    
    # ML & Recommendation Outputs
    conversion_probability: Optional[float] = None
    lead_score: Optional[int] = None
    recommended_action: Optional[str] = None
