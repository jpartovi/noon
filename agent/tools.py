"""Tool definitions for the calendar scheduling agent."""

from datetime import datetime
from typing import List, Dict, Any
from langchain_core.tools import tool
from agent.mocks import (
    generate_mock_events,
    generate_mock_event,
    generate_mock_calendars,
)


# Internal tools - gather information without terminating
@tool
def read_schedule(start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """
    Read events from the schedule within a time window.
    
    Args:
        start_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T00:00:00-08:00")
        end_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T23:59:59-08:00")
    
    Returns:
        List of events with minimal details (id, summary, start, end, calendar_id)
    """
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    
    events = generate_mock_events(start_dt, end_dt, count=3)
    
    # Return minimal details
    return [
        {
            "id": event["id"],
            "summary": event["summary"],
            "start": event["start"],
            "end": event["end"],
            "calendar_id": event["calendar_id"],
        }
        for event in events
    ]


@tool
def search_events(keywords: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
    """
    Search for events matching keywords within a time window.
    
    Args:
        keywords: Space-separated keywords to search for
        start_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T00:00:00-08:00")
        end_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T23:59:59-08:00")
    
    Returns:
        List of matching events with minimal details
    """
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    
    keyword_list = keywords.split()
    events = generate_mock_events(start_dt, end_dt, count=2, keywords=keyword_list)
    
    return [
        {
            "id": event["id"],
            "summary": event["summary"],
            "start": event["start"],
            "end": event["end"],
            "calendar_id": event["calendar_id"],
        }
        for event in events
    ]


@tool
def read_event(event_id: str, calendar_id: str) -> Dict[str, Any]:
    """
    Read detailed information about a specific event.
    
    Args:
        event_id: The ID of the event to read
        calendar_id: The ID of the calendar containing the event
    
    Returns:
        Detailed event information
    """
    return generate_mock_event(event_id=event_id, calendar_id=calendar_id)


@tool
def list_calendars() -> List[Dict[str, Any]]:
    """
    List all available calendars.
    
    Returns:
        List of calendars with their details
    """
    return generate_mock_calendars()


# External tools - terminate agent and return response
@tool
def show_schedule(start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Show the schedule to the user. This terminates the agent.
    
    Args:
        start_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T00:00:00-08:00")
        end_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T23:59:59-08:00")
    
    Returns:
        Dict with type "show-schedule" and metadata
    """
    return {
        "type": "show-schedule",
        "metadata": {
            "start-date": start_time,
            "end-date": end_time,
        },
    }


@tool
def show_event(event_id: str, calendar_id: str) -> Dict[str, Any]:
    """
    Show a specific event to the user. This terminates the agent.
    
    Args:
        event_id: The ID of the event to show
        calendar_id: The ID of the calendar containing the event
    
    Returns:
        Dict with type "show-event" and metadata
    """
    return {
        "type": "show-event",
        "metadata": {
            "event-id": event_id,
            "calendar-id": calendar_id,
        },
    }


@tool
def request_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str,
    description: str = None,
    location: str = None,
) -> Dict[str, Any]:
    """
    Request to create a new event. This terminates the agent.
    
    Args:
        summary: Title/summary of the event
        start_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T10:00:00-08:00")
        end_time: Timezone-aware ISO format datetime string with offset (e.g., "2026-01-14T11:00:00-08:00")
        calendar_id: ID of the calendar to create the event on
        description: Optional description of the event
        location: Optional location for the event
    
    Returns:
        Dict with type "create-event" and metadata
    """
    metadata = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": end_time, "timeZone": "America/Los_Angeles"},
        "calendar_id": calendar_id,
    }
    
    if description:
        metadata["description"] = description
    if location:
        metadata["location"] = location
    
    return {
        "type": "create-event",
        "metadata": metadata,
    }


@tool
def request_update_event(
    event_id: str,
    calendar_id: str,
    summary: str = None,
    start_time: str = None,
    end_time: str = None,
    description: str = None,
    location: str = None,
) -> Dict[str, Any]:
    """
    Request to update an existing event. This terminates the agent.
    
    Args:
        event_id: The ID of the event to update
        calendar_id: The ID of the calendar containing the event
        summary: Optional new summary/title
        start_time: Optional new start time (timezone-aware ISO format datetime string with offset, e.g., "2026-01-14T10:00:00-08:00")
        end_time: Optional new end time (timezone-aware ISO format datetime string with offset, e.g., "2026-01-14T11:00:00-08:00")
        description: Optional new description
        location: Optional new location
    
    Returns:
        Dict with type "update-event" and metadata
    """
    metadata = {
        "event-id": event_id,
        "calendar-id": calendar_id,
    }
    
    if summary:
        metadata["summary"] = summary
    if start_time:
        metadata["start"] = {"dateTime": start_time, "timeZone": "America/Los_Angeles"}
    if end_time:
        metadata["end"] = {"dateTime": end_time, "timeZone": "America/Los_Angeles"}
    if description:
        metadata["description"] = description
    if location:
        metadata["location"] = location
    
    return {
        "type": "update-event",
        "metadata": metadata,
    }


@tool
def request_delete_event(event_id: str, calendar_id: str) -> Dict[str, Any]:
    """
    Request to delete an event. This terminates the agent.
    
    Args:
        event_id: The ID of the event to delete
        calendar_id: The ID of the calendar containing the event
    
    Returns:
        Dict with type "delete-event" and metadata
    """
    return {
        "type": "delete-event",
        "metadata": {
            "event-id": event_id,
            "calendar-id": calendar_id,
        },
    }


@tool
def do_nothing(reason: str) -> Dict[str, Any]:
    """
    Do nothing and terminate the agent. Use this when the request cannot be fulfilled
    or is not supported.
    
    Args:
        reason: Explanation of why no action is being taken
    
    Returns:
        Dict with type "no-action" and metadata
    """
    return {
        "type": "no-action",
        "metadata": {
            "reason": reason,
        },
    }


# Lists of tools for easy access
INTERNAL_TOOLS = [read_schedule, search_events, read_event, list_calendars]
EXTERNAL_TOOLS = [
    show_schedule,
    show_event,
    request_create_event,
    request_update_event,
    request_delete_event,
    do_nothing,
]
ALL_TOOLS = INTERNAL_TOOLS + EXTERNAL_TOOLS
