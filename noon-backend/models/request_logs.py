"""Database models for request_logs table."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, IPvAnyAddress


class RequestLogBase(BaseModel):
    """Base request log fields."""

    endpoint: str = Field(..., description="API endpoint (e.g., '/agent/chat')")
    method: str = Field(default="POST", description="HTTP method")
    request_body: Optional[Dict[str, Any]] = Field(
        None, description="Full request payload (JSONB)"
    )
    request_headers: Optional[Dict[str, Any]] = Field(
        None, description="Relevant headers (user-agent, etc.)"
    )
    response_status: Optional[int] = Field(
        None,
        ge=100,
        lt=600,
        description="HTTP status code (100-599)",
    )
    response_body: Optional[Dict[str, Any]] = Field(
        None, description="Response payload (JSONB)"
    )
    response_time_ms: Optional[int] = Field(
        None, ge=0, description="Response time in milliseconds"
    )
    agent_action: Optional[str] = Field(
        None,
        description="Agent action ('create', 'read', 'update', 'delete', 'search', 'schedule')",
    )
    agent_tool: Optional[str] = Field(None, description="Tool name that was called")
    agent_success: Optional[bool] = Field(
        None, description="Whether agent operation succeeded"
    )
    agent_summary: Optional[str] = Field(
        None, description="Human-readable summary from agent"
    )
    intent_category: Optional[str] = Field(
        None,
        description="Extracted intent category (e.g., 'schedule_meeting', 'view_calendar')",
    )
    entities: Optional[Dict[str, Any]] = Field(
        None, description="Extracted entities (people, times, locations, etc.) - JSONB"
    )
    user_pattern: Optional[str] = Field(
        None, description="Identified user pattern/rule"
    )
    ip_address: Optional[str] = Field(
        None, description="Client IP address (inet type)"
    )
    user_agent: Optional[str] = Field(None, description="User agent string")


class RequestLogCreate(RequestLogBase):
    """Schema for creating a new request log."""

    user_id: UUID = Field(..., description="User ID who made the request")


class RequestLogUpdate(BaseModel):
    """Schema for updating request log fields (for async processing)."""

    response_status: Optional[int] = Field(None, ge=100, lt=600)
    response_body: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = Field(None, ge=0)
    agent_action: Optional[str] = None
    agent_tool: Optional[str] = None
    agent_success: Optional[bool] = None
    agent_summary: Optional[str] = None
    intent_category: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    user_pattern: Optional[str] = None


class RequestLog(RequestLogBase):
    """
    Complete request log model matching Supabase 'request_logs' table.

    Used for tracking user interactions and building patterns/rulesets.
    """

    id: UUID
    user_id: UUID
    endpoint: str
    method: str = "POST"
    request_body: Optional[Dict[str, Any]] = None
    request_headers: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    agent_action: Optional[str] = None
    agent_tool: Optional[str] = None
    agent_success: Optional[bool] = None
    agent_summary: Optional[str] = None
    intent_category: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    user_pattern: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Metadata
    created_at: datetime

    class Config:
        from_attributes = True

