"""
SQLModel definition for the Feedback entity.
Records human-in-the-loop interactions (accept/override).
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: str = Field(index=True, description="Unique lead identifier")
    original_action: str = Field(description="The original recommended action")
    override_action: Optional[str] = Field(default=None, description="The human override action, if any")
    reason: Optional[str] = Field(default=None, description="Free-text reason for the override")
    timestamp: datetime = Field(default_factory=utc_now)
    actor_context: Optional[str] = Field(default=None, description="Identity of the actor (limitation: currently unauthenticated system)")
