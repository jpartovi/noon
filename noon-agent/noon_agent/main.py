"""Noon agent - Simple Google Calendar operations with LangGraph."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .gcal_wrapper import (
    get_calendar_service,
    create_calendar_event,
    read_calendar_events,
    search_calendar_events,
    update_calendar_event,
    delete_calendar_event,
)


class State(TypedDict, total=False):
    """Internal state propagated between graph nodes."""

    action: Literal["create", "delete", "update", "read", "search"]
    start_time: datetime | None
    end_time: datetime | None
    event_id: str | None
    query: str | None
    auth: Dict[str, Any]
    summary: str
    description: str | None


class OutputState(TypedDict):
    """Output state returned by the graph."""

    summary: str


def route_action(state: State) -> str:
    """Select the next node based on requested action; default to read."""
    return state.get("action", "read")


def _with_summary(state: State, message: str) -> State:
    """Helper to add summary to state."""
    next_state = dict(state)
    next_state["summary"] = message
    return next_state


def create_event(state: State) -> State:
    """Create a calendar event using Google Calendar API."""
    try:
        service = get_calendar_service()

        result = create_calendar_event(
            service=service,
            summary=state.get("summary", "New Event"),
            start_time=state.get("start_time"),
            end_time=state.get("end_time"),
            description=state.get("description"),
        )

        if result["status"] == "success":
            message = f"Created event: {result['summary']} at {result['start']}"
        else:
            message = f"Failed to create event: {result.get('error', 'Unknown error')}"

        return _with_summary(state, message)
    except Exception as e:
        return _with_summary(state, f"Error creating event: {str(e)}")


def read_event(state: State) -> State:
    """Read/list calendar events using Google Calendar API."""
    try:
        service = get_calendar_service()

        result = read_calendar_events(
            service=service,
            time_min=state.get("start_time"),
            time_max=state.get("end_time"),
        )

        if result["status"] == "success":
            event_list = "\n".join([
                f"- {e['summary']} at {e['start']}"
                for e in result["events"]
            ])
            message = f"Found {result['count']} events:\n{event_list}" if result["count"] > 0 else "No events found."
        else:
            message = f"Failed to read events: {result.get('error', 'Unknown error')}"

        return _with_summary(state, message)
    except Exception as e:
        return _with_summary(state, f"Error reading events: {str(e)}")


def update_event(state: State) -> State:
    """Update a calendar event using Google Calendar API."""
    try:
        service = get_calendar_service()

        result = update_calendar_event(
            service=service,
            event_id=state.get("event_id"),
            summary=state.get("summary"),
            start_time=state.get("start_time"),
            end_time=state.get("end_time"),
            description=state.get("description"),
        )

        if result["status"] == "success":
            message = f"Updated event: {result['summary']}"
        else:
            message = f"Failed to update event: {result.get('error', 'Unknown error')}"

        return _with_summary(state, message)
    except Exception as e:
        return _with_summary(state, f"Error updating event: {str(e)}")


def delete_event(state: State) -> State:
    """Delete a calendar event using Google Calendar API."""
    try:
        service = get_calendar_service()

        result = delete_calendar_event(
            service=service,
            event_id=state.get("event_id"),
        )

        if result["status"] == "success":
            message = result["message"]
        else:
            message = f"Failed to delete event: {result.get('error', 'Unknown error')}"

        return _with_summary(state, message)
    except Exception as e:
        return _with_summary(state, f"Error deleting event: {str(e)}")


def search_event(state: State) -> State:
    """Search calendar events using free text query."""
    try:
        service = get_calendar_service()

        result = search_calendar_events(
            service=service,
            query=state.get("query", ""),
            time_min=state.get("start_time"),
            time_max=state.get("end_time"),
        )

        if result["status"] == "success":
            if result["count"] > 0:
                event_list = "\n".join([
                    f"- {e['summary']} at {e['start']}"
                    for e in result["events"]
                ])
                message = f"Found {result['count']} events matching '{state.get('query')}':\n{event_list}"
            else:
                message = f"No events found matching '{state.get('query')}'"
        else:
            message = f"Failed to search events: {result.get('error', 'Unknown error')}"

        return _with_summary(state, message)
    except Exception as e:
        return _with_summary(state, f"Error searching events: {str(e)}")


# Build the graph
graph_builder = StateGraph(State, output_schema=OutputState)
graph_builder.add_node("create", create_event)
graph_builder.add_node("read", read_event)
graph_builder.add_node("search", search_event)
graph_builder.add_node("update", update_event)
graph_builder.add_node("delete", delete_event)

graph_builder.add_conditional_edges(
    START,
    route_action,
    {
        "create": "create",
        "read": "read",
        "search": "search",
        "update": "update",
        "delete": "delete",
    },
)

for action in ("create", "read", "search", "update", "delete"):
    graph_builder.add_edge(action, END)

graph = graph_builder.compile(name="noon-agent")


def build_agent_graph() -> StateGraph:
    """Return the compiled calendar agent graph."""
    return graph


def invoke_agent(state: State) -> OutputState:
    """Invoke the calendar agent with the given state."""
    result = graph.invoke(state)
    return {"summary": result.get("summary", "")}




# other ideas
# • - search_free_time – scan attendee calendars for the
#     earliest mutually available windows.
#   - propose_slots – generate a ranked shortlist
#     of candidate start/end times (with time‑zone
#     normalization).
#   - adjust_event – move an existing event by
#     ±N minutes/hours while keeping participant
#     constraints intact.
#   - sync_external – pull in events from external
#     sources (invites, shared calendars) and reconcile
#     duplicates.
#   - notify_attendees – draft/send updates or reminders
#     when an event is created, moved, or canceled.
#   - summarize_day – return a natural-language rundown
#     of the user’s schedule, conflicts, and gaps.
#   - set_preferences – store user defaults (meeting
#     lengths, working hours, buffer rules) for
#     downstream actions.
#   - resolve_conflict – pick which overlapping event
#     to keep, reschedule, or decline based on priority
#     rules.
#   - collect_requirements – gather missing metadata
#     (agenda, location, video link) before finalizing
#     an event.
