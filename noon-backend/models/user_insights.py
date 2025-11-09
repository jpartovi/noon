"""Database models for user_insights table."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserInsightBase(BaseModel):
    """Base user insight fields."""

    insight_type: str = Field(
        ...,
        description="Type of insight: 'preference', 'habit', 'pattern', 'goal', 'constraint'",
    )
    category: str = Field(
        ...,
        description="Category: 'schedule', 'meetings', 'health', 'work', 'personal', etc.",
    )
    key: str = Field(..., description="Unique key for this insight within category")
    value: Dict[str, Any] = Field(..., description="Flexible JSONB value for the insight")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="LLM confidence score (0.0 to 1.0)",
    )
    source: str = Field(
        default="agent",
        description="Source: 'agent' (LLM), 'pattern_analysis', 'explicit' (user set)",
    )
    source_request_id: Optional[UUID] = Field(
        None, description="ID of request that generated this insight"
    )


class UserInsightCreate(UserInsightBase):
    """Schema for creating a new user insight."""

    user_id: UUID = Field(..., description="User ID")


class UserInsightUpdate(BaseModel):
    """Schema for updating user insight fields."""

    value: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source: Optional[str] = None


class UserInsight(UserInsightBase):
    """
    Complete user insight model matching Supabase 'user_insights' table.

    Stores LLM-discovered user preferences, habits, and patterns.
    """

    id: UUID
    user_id: UUID
    insight_type: str
    category: str
    key: str
    value: Dict[str, Any]
    confidence: float = 0.5
    source: str = "agent"
    source_request_id: Optional[UUID] = None

    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

