from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, description="Foreign key to Lead.lead_id")
    interaction_type: str = Field(description="Type of interaction: email_opened, call_made, web_visit, etc.")
    timestamp: datetime = Field(default_factory=utc_now)
    duration: Optional[int] = Field(default=0, description="Duration in seconds, if applicable")
