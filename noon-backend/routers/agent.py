"""Agent router for calendar operations."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import AuthenticatedUser, get_current_user
from schemas import agent as agent_schema
from services.calendar_agent import (
    CalendarAgentError,
    CalendarAgentUserError,
    calendar_agent_service,
)

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=agent_schema.AgentChatResponse)
async def chat_with_agent(
    payload: agent_schema.AgentChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> agent_schema.AgentChatResponse:
    """
    Chat with the calendar agent.

    Accepts natural language input and returns structured JSON with:
    - tool: The action/tool that was called
    - summary: Human-readable summary
    - result: Full tool result (if available)
    - success: Whether the operation succeeded
    """
    try:
        result = calendar_agent_service.chat(
            user_id=current_user.id, message=payload.text
        )
        return agent_schema.AgentChatResponse(**result)
    except CalendarAgentUserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CalendarAgentError as exc:
        logger.exception("Error invoking agent for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
