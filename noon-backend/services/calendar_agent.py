"""Service wrapper around the Noon calendar agent."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def _import_agent_components():
    """Ensure the noon-agent package is importable and return required symbols."""

    agent_root = Path(__file__).resolve().parents[2] / "noon-agent"
    if not agent_root.exists():
        raise ImportError(f"Could not locate noon-agent at {agent_root}")
    agent_path = str(agent_root)
    if agent_path not in sys.path:
        sys.path.insert(0, agent_path)

    try:
        from noon_agent.main import graph  # type: ignore
        from noon_agent.db_context import load_user_context_from_db  # type: ignore
    except ImportError as exc:  # pragma: no cover - startup failure
        raise ImportError("Failed to import noon-agent modules") from exc

    return graph, load_user_context_from_db


class CalendarAgentError(RuntimeError):
    """Base error raised when the calendar agent invocation fails."""


class CalendarAgentUserError(CalendarAgentError):
    """Raised when a user-specific precondition fails (e.g., missing token)."""


class CalendarAgentService:
    """Encapsulates invocation of the Noon LangGraph calendar agent."""

    def __init__(
        self,
        *,
        graph: Optional[Any] = None,
        load_user_context: Optional[Any] = None,
    ) -> None:
        if graph is None or load_user_context is None:
            default_graph, default_loader = _import_agent_components()
            graph = graph or default_graph
            load_user_context = load_user_context or default_loader

        self._graph = graph
        self._load_user_context = load_user_context

    def _build_agent_state(
        self, *, message: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the agent state object expected by noon-agent."""

        access_token = user_context.get("access_token")
        if not access_token:
            raise CalendarAgentUserError(
                "User has no Google Calendar access token. Please link your Google account first."
            )

        google_account = user_context.get("google_account")
        if not google_account:
            logger.warning(
                "CALENDAR_AGENT_SERVICE: No google_account context for user %s", user_context.get("user_id", "<unknown>")
            )

        context = {
            "primary_calendar_id": user_context.get("primary_calendar_id", "primary"),
            "timezone": user_context.get("timezone", "UTC"),
            "all_calendar_ids": user_context.get("all_calendar_ids", []),
            "friends": user_context.get("friends", []),
        }
        if google_account:
            context["google_account"] = google_account

        query_text = message.strip()
        if not query_text:
            raise CalendarAgentUserError("Transcription was empty. Try speaking again.")

        state: State = {
            "query": query_text,
            "auth_token": access_token,
            "context": context,
        }
        logger.info(
            "CALENDAR_AGENT_SERVICE: Prepared state for user %s (has_token=%s)",
            user_context.get("user_id", "<unknown>"),
            bool(access_token),
        )
        return state

    def _load_context(self, user_id: str) -> Dict[str, Any]:
        try:
            return self._load_user_context(user_id)
        except ValueError as exc:
            raise CalendarAgentUserError(str(exc)) from exc

    def chat(self, *, user_id: str, message: str) -> Dict[str, Any]:
        """
        Invoke the calendar agent for the given user and message.

        Returns:
            Dict with tool, summary, result, success keys to match API schema.
        """

        if not message:
            raise CalendarAgentUserError("Message text cannot be empty.")

        user_context = self._load_context(user_id)
        state = self._build_agent_state(message=message, user_context=user_context)

        logger.info("CALENDAR_AGENT_SERVICE: invoking agent graph for user %s", user_id)
        try:
            final_state = self._graph.invoke(state)
        except Exception as exc:
            logger.exception(
                "Calendar agent graph invocation failed for user %s", user_id
            )
            raise CalendarAgentError(f"Agent invocation failed: {exc}") from exc

        agent_payload = final_state.get("agent_result")
        if agent_payload is None:
            raise CalendarAgentError("Agent completed without returning a result payload")

        if isinstance(agent_payload, BaseModel):
            result_dict = agent_payload.model_dump(exclude_none=True)
        elif isinstance(agent_payload, dict):
            result_dict = {k: v for k, v in agent_payload.items() if v is not None}
        else:
            raise CalendarAgentError("Agent returned an unsupported payload type")

        tool_name = result_dict.get("tool", "read")
        summary = _summarize_agent_payload(result_dict)

        return {
            "tool": tool_name,
            "summary": summary,
            "result": result_dict,
            "success": True,
        }


def _summarize_agent_payload(payload: Dict[str, Any]) -> str:
    tool = payload.get("tool")
    if tool == "create":
        return f"Prepare to create '{payload.get('summary', 'event')}'"
    if tool == "update":
        return f"Prepare to update event {payload.get('id', '')}"
    if tool == "delete":
        return f"Prepare to delete event {payload.get('id', '')}"
    if tool == "show":
        query = payload.get("event", {}).get("query")
        return f"Show event instructions for '{query or payload.get('id', '')}'"
    if tool == "show-schedule":
        return f"Show schedule from {payload.get('start_day')} to {payload.get('end_day')}"
    return "Agent instructions ready"


class _CalendarAgentServiceProxy:
    """Lazy loader that instantiates the real service on first use."""

    def __init__(self):
        self._service: CalendarAgentService | None = None

    def _ensure(self) -> CalendarAgentService:
        if self._service is None:
            self._service = CalendarAgentService()
        return self._service

    def __getattr__(self, item):
        return getattr(self._ensure(), item)


calendar_agent_service = _CalendarAgentServiceProxy()

__all__ = [
    "calendar_agent_service",
    "CalendarAgentService",
    "CalendarAgentError",
    "CalendarAgentUserError",
]
