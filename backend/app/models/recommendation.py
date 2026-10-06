from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, description="Foreign key to Lead.lead_id")
    recommended_action: str = Field(description="The deterministic next best action")
    recommendation_confidence: float = Field(description="Confidence score for the recommendation")
    timestamp: datetime = Field(default_factory=utc_now)
