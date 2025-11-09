"""Service for logging agent/LLM observability data."""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from models.agent_observability import AgentObservabilityCreate
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AgentObservabilityService:
    """Service for logging LangGraph agent calls and LLM interactions."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def log_agent_call(
        self,
        user_id: UUID | str,
        agent_action: str,
        user_message: str,
        agent_response: Optional[str] = None,
        agent_tool: Optional[str] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_prompt_tokens: Optional[int] = None,
        llm_completion_tokens: Optional[int] = None,
        llm_total_tokens: Optional[int] = None,
        llm_cost_usd: Optional[Decimal | float] = None,
        intent_category: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an agent/LLM call for observability.

        Args:
            user_id: User ID
            agent_action: Agent action ('create', 'read', 'update', 'delete', 'search', 'schedule')
            user_message: User's input message
            agent_response: Agent's response/summary
            agent_tool: Tool name that was called
            agent_state: Full agent state at execution
            tool_result: Tool execution result
            execution_time_ms: Total execution time
            success: Whether operation succeeded
            error_message: Error if failed
            agent_run_id: LangGraph run ID for tracing
            llm_model: Model used
            llm_prompt_tokens: Tokens in prompt
            llm_completion_tokens: Tokens in completion
            llm_total_tokens: Total tokens
            llm_cost_usd: Estimated cost in USD
            intent_category: Extracted intent
            entities: Extracted entities

        Returns:
            Observability record ID
        """
        try:
            # Convert Decimal to float for JSON serialization
            cost = float(llm_cost_usd) if llm_cost_usd else None

            observability_data = AgentObservabilityCreate(
                user_id=str(user_id),
                agent_run_id=agent_run_id,
                agent_action=agent_action,
                agent_tool=agent_tool,
                llm_model=llm_model,
                llm_prompt_tokens=llm_prompt_tokens,
                llm_completion_tokens=llm_completion_tokens,
                llm_total_tokens=llm_total_tokens,
                llm_cost_usd=Decimal(str(cost)) if cost else None,
                user_message=user_message,
                agent_response=agent_response,
                agent_state=agent_state,
                tool_result=tool_result,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message,
                intent_category=intent_category,
                entities=entities,
            )

            result = (
                self.supabase.table("agent_observability")
                .insert(observability_data.model_dump(exclude_none=True))
                .execute()
            )

            if result.data:
                record_id = result.data[0]["id"]
                logger.debug(f"Logged agent call {record_id} for user {user_id}")
                return record_id
            else:
                raise ValueError("Failed to create observability record")

        except Exception as e:
            logger.error(f"Failed to log agent call: {e}", exc_info=True)
            # Don't raise - observability logging should not break the main flow
            return ""


# Singleton instance
agent_observability_service = AgentObservabilityService()

