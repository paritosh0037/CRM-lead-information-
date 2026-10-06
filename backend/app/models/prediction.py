from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, description="Foreign key to Lead.lead_id")
    conversion_probability: float = Field(description="Predicted probability of conversion")
    lead_score: int = Field(description="Scaled integer score 0-100")
    timestamp: datetime = Field(default_factory=utc_now)
