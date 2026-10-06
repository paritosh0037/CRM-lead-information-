from typing import Optional
from sqlmodel import SQLModel, Field

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, unique=True, description="Unique lead identifier")
    
    # Core CRM Profile
    annual_revenue: Optional[float] = 0.0
    budget: Optional[float] = 0.0
    deal_value: Optional[float] = 0.0
    industry: Optional[str] = None
    company_size: Optional[str] = None
    lead_source: Optional[str] = None
    opportunity_stage: Optional[str] = None
