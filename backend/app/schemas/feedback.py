from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FeedbackAcceptInput(BaseModel):
    """Input schema for accepting a recommendation."""
    original_action: str = Field(..., description="The original recommended action")
    actor_context: Optional[str] = Field(None, description="Actor context if available")

class FeedbackOverrideInput(BaseModel):
    """Input schema for overriding a recommendation."""
    original_action: str = Field(..., description="The original recommended action")
    override_action: str = Field(..., description="The human selected action (CALL, EMAIL, DEMO, NURTURE, REVIEW)")
    reason: str = Field(..., min_length=1, description="Free-text reason for the override")
    actor_context: Optional[str] = Field(None, description="Actor context if available")

class FeedbackResponse(BaseModel):
    """Response schema for a feedback record."""
    id: int
    lead_id: str
    original_action: str
    override_action: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime
    actor_context: Optional[str] = None
