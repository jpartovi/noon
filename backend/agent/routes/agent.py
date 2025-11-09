"""Agent endpoint for invoking the LangGraph calendar agent."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langgraph_sdk import get_client

from schemas.user import AuthenticatedUser
from schemas.agent_response import AgentResponse
from dependencies import get_current_user
from auth.utils.supabase_client import get_google_account
from config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentActionRequest(BaseModel):
    """Request to invoke the calendar agent."""
    query: str


@router.post("/action", response_model=AgentResponse)
async def agent_action(
    payload: AgentActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Invoke the LangGraph calendar agent with a natural language query.

    The agent will classify intent and extract metadata for calendar operations.
    """
    try:
        # Get user's Google OAuth tokens from Supabase
        google_account = await get_google_account(current_user.id)
        if not google_account:
            raise HTTPException(
                status_code=400,
                detail="No Google account linked. Please connect a Google account first."
            )

        # Prepare auth data with Google tokens
        auth = {
            "user_id": current_user.id,
            "google_tokens": google_account.get("tokens", {})
        }

        # Create LangGraph SDK client and invoke agent
        settings = get_settings()
        client = get_client(url=settings.langgraph_agent_url)

        input_state = {
            "query": payload.query,
            "auth": auth,
            "success": False,
            "request": "no-action",
            "metadata": {}
        }

        logger.info(f"Invoking agent for user {current_user.id} with query: {payload.query[:50]}...")

        # Invoke and wait for completion
        result = await client.runs.wait(
            thread_id=None,
            assistant_id="agent",
            input=input_state,
        )

        logger.info(f"Agent completed. Request: {result.get('request')}, Success: {result.get('success')}")

        return {
            "success": result.get("success", False),
            "request": result.get("request", "no-action"),
            "metadata": result.get("metadata", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke agent: {str(e)}"
        )
