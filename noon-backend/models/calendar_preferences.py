"""Database models for calendar_preferences table."""

from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarPreferenceBase(BaseModel):
    """Base calendar preference fields."""

    preference_type: str = Field(
        ...,
        description="Type: 'gym', 'sleep', 'focus', 'meal', 'break', 'meditation', etc.",
    )
    title: str = Field(..., description="Title for the preference (e.g., 'Morning Gym')")
    description: Optional[str] = Field(None, description="Optional description")
    day_of_week: Optional[List[int]] = Field(
        None,
        description="Days of week (1=Mon, 7=Sun), empty/null = daily",
    )
    start_time: time = Field(..., description="Preferred start time")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    timezone: str = Field(default="UTC", description="Timezone")
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority 1 (highest) to 10 (lowest)",
    )
    is_flexible: bool = Field(
        default=True, description="Can be moved if conflicts occur"
    )
    buffer_before_minutes: int = Field(
        default=0, ge=0, description="Buffer before event in minutes"
    )
    buffer_after_minutes: int = Field(
        default=0, ge=0, description="Buffer after event in minutes"
    )
    auto_schedule: bool = Field(
        default=False, description="Automatically add to calendar"
    )
    calendar_id: Optional[str] = Field(
        None, description="Which calendar to add to (null = primary)"
    )
    source: str = Field(
        default="insight",
        description="Source: 'insight' (from LLM), 'explicit' (user set), 'pattern' (analyzed)",
    )
    source_insight_id: Optional[UUID] = Field(
        None, description="ID of insight that generated this preference"
    )
    is_active: bool = Field(default=True, description="Whether this preference is active")


class CalendarPreferenceCreate(CalendarPreferenceBase):
    """Schema for creating a new calendar preference."""

    user_id: UUID = Field(..., description="User ID")


class CalendarPreferenceUpdate(BaseModel):
    """Schema for updating calendar preference fields."""

    title: Optional[str] = None
    description: Optional[str] = None
    day_of_week: Optional[List[int]] = None
    start_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    timezone: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_flexible: Optional[bool] = None
    buffer_before_minutes: Optional[int] = Field(None, ge=0)
    buffer_after_minutes: Optional[int] = Field(None, ge=0)
    auto_schedule: Optional[bool] = None
    calendar_id: Optional[str] = None
    is_active: Optional[bool] = None


class CalendarPreference(CalendarPreferenceBase):
    """
    Complete calendar preference model matching Supabase 'calendar_preferences' table.

    Used for recurring events/activities (gym, sleep, focus blocks) for auto-scheduling.
    """

    id: UUID
    user_id: UUID
    preference_type: str
    title: str
    description: Optional[str] = None
    day_of_week: Optional[List[int]] = None
    start_time: time
    duration_minutes: int
    timezone: str = "UTC"
    priority: int = 5
    is_flexible: bool = True
    buffer_before_minutes: int = 0
    buffer_after_minutes: int = 0
    auto_schedule: bool = False
    calendar_id: Optional[str] = None
    source: str = "insight"
    source_insight_id: Optional[UUID] = None
    is_active: bool = True

    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

