"""Database models for agent_observability table."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentObservabilityBase(BaseModel):
    """Base agent observability fields."""

    agent_run_id: Optional[str] = Field(None, description="LangGraph run ID for tracing")
    agent_action: str = Field(
        ...,
        description="Agent action: 'create', 'read', 'update', 'delete', 'search', 'schedule'",
    )
    agent_tool: Optional[str] = Field(None, description="Tool name that was called")
    llm_model: Optional[str] = Field(None, description="Model used (e.g., 'gpt-4o-mini')")
    llm_prompt_tokens: Optional[int] = Field(None, ge=0, description="Tokens in prompt")
    llm_completion_tokens: Optional[int] = Field(None, ge=0, description="Tokens in completion")
    llm_total_tokens: Optional[int] = Field(None, ge=0, description="Total tokens")
    llm_cost_usd: Optional[Decimal] = Field(None, description="Estimated cost in USD")
    user_message: str = Field(..., description="User's input message")
    agent_response: Optional[str] = Field(None, description="Agent's response/summary")
    agent_state: Optional[Dict[str, Any]] = Field(None, description="Full agent state at execution")
    tool_result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Total execution time")
    success: bool = Field(default=True, description="Whether operation succeeded")
    error_message: Optional[str] = Field(None, description="Error if failed")
    intent_category: Optional[str] = Field(None, description="Extracted intent")
    entities: Optional[Dict[str, Any]] = Field(None, description="Extracted entities")


class AgentObservabilityCreate(AgentObservabilityBase):
    """Schema for creating a new agent observability record."""

    user_id: UUID = Field(..., description="User ID")


class AgentObservability(AgentObservabilityBase):
    """
    Complete agent observability model matching Supabase 'agent_observability' table.

    Tracks LangGraph agent calls and LLM interactions for observability.
    """

    id: UUID
    user_id: UUID
    agent_run_id: Optional[str] = None
    agent_action: str
    agent_tool: Optional[str] = None
    llm_model: Optional[str] = None
    llm_prompt_tokens: Optional[int] = None
    llm_completion_tokens: Optional[int] = None
    llm_total_tokens: Optional[int] = None
    llm_cost_usd: Optional[Decimal] = None
    user_message: str
    agent_response: Optional[str] = None
    agent_state: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    intent_category: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime

    class Config:
        from_attributes = True

