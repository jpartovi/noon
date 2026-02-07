"""Mock data generators for calendar agent tools."""

from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_mock_calendars() -> List[Dict[str, Any]]:
    """Generate a mock list of calendars."""
    return [
        {
            "id": "primary",
            "name": "Primary Calendar",
            "summary": "Primary Calendar",
            "description": "My primary calendar",
            "timezone": "America/Los_Angeles",
            "color": "#7986CB",
            "is_primary": True,
            "access_role": "owner",
        },
        {
            "id": "work@group.calendar.google.com",
            "name": "Work Calendar",
            "summary": "Work Calendar",
            "description": "Work events",
            "timezone": "America/Los_Angeles",
            "color": "#F4511E",
            "is_primary": False,
            "access_role": "writer",
        },
        {
            "id": "personal@group.calendar.google.com",
            "name": "Personal Calendar",
            "summary": "Personal Calendar",
            "description": "Personal events",
            "timezone": "America/Los_Angeles",
            "color": "#33B679",
            "is_primary": False,
            "access_role": "writer",
        },
    ]


# Fixed events for February 2026 (test date is Monday Feb 9, 2026 at 10am PST)
# These events cover:
# - Feb 9 (Monday/today): Team Meeting, Lunch, Lunch with Sarah, Meeting at 3pm, Doctor Appointment, Haircut
# - Feb 10 (Tuesday/tomorrow): Dinner
# - Feb 13 (Friday): Additional Lunch with Sarah for Friday queries
FIXED_EVENTS_2026_02 = [
    # Feb 9, 2026 (Monday - test day "today")
    {
        "id": "event_001",
        "summary": "Team Meeting",
        "description": "Mock event: Team Meeting",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T09:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T10:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_001",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    {
        "id": "event_002",
        "summary": "Lunch",
        "description": "Mock event: Lunch",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T12:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T13:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_002",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    {
        "id": "event_003",
        "summary": "Coffee with Sarah",
        "description": "Mock event: Coffee with Sarah",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T12:30:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T13:30:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_003",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    {
        "id": "event_004",
        "summary": "Meeting",
        "description": "Mock event: Meeting at 3pm",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T15:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T16:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_004",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    {
        "id": "event_005",
        "summary": "Doctor Appointment",
        "description": "Mock event: Doctor Appointment",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T16:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T17:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_005",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    {
        "id": "event_006",
        "summary": "Haircut",
        "description": "Mock event: Haircut appointment",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-09T17:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-09T18:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_006",
        "hangout_link": None,
        "updated": "2026-02-09T00:00:00-08:00",
    },
    # Feb 10, 2026 (Tuesday - "tomorrow")
    {
        "id": "event_007",
        "summary": "Dinner",
        "description": "Mock event: Dinner",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-10T19:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-10T20:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_007",
        "hangout_link": None,
        "updated": "2026-02-10T00:00:00-08:00",
    },
    # Feb 13, 2026 (Friday)
    {
        "id": "event_008",
        "summary": "Friday Standup",
        "description": "Mock event: Friday team standup",
        "status": "confirmed",
        "start": {
            "dateTime": "2026-02-13T09:00:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": "2026-02-13T09:30:00-08:00",
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": "primary",
        "calendar_name": "Primary Calendar",
        "html_link": "https://calendar.google.com/event?eid=event_008",
        "hangout_link": None,
        "updated": "2026-02-13T00:00:00-08:00",
    },
]


def generate_mock_event(
    event_id: str = None,
    calendar_id: str = None,
    summary: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
) -> Dict[str, Any]:
    """Generate a mock calendar event.

    If event_id matches a known fixed event, return that event's details.
    Otherwise, generate a default event.
    """
    # Check if this is a known event
    if event_id:
        for event in FIXED_EVENTS_2026_02:
            if event["id"] == event_id:
                # Return a copy with potentially overridden calendar_id
                result = event.copy()
                if calendar_id:
                    result["calendar_id"] = calendar_id
                return result

    if event_id is None:
        event_id = "event_default_001"
    if calendar_id is None:
        calendars = generate_mock_calendars()
        calendar_id = calendars[0]["id"]

    if start_time is None:
        # Default to 2/9/2026 10:00 AM PST
        start_time = datetime(2026, 2, 9, 10, 0, 0)
    if end_time is None:
        end_time = start_time + timedelta(hours=1)

    if summary is None:
        summary = "Default Event"

    return {
        "id": event_id,
        "summary": summary,
        "description": f"Mock event: {summary}",
        "status": "confirmed",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "America/Los_Angeles",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "America/Los_Angeles",
        },
        "calendar_id": calendar_id,
        "calendar_name": "Primary Calendar",
        "html_link": f"https://calendar.google.com/event?eid={event_id}",
        "hangout_link": None,
        "updated": datetime(2026, 2, 9, 0, 0, 0).isoformat(),
    }


def generate_mock_events(
    start_time: datetime,
    end_time: datetime,
    count: int = 10,
    keywords: List[str] = None,
) -> List[Dict[str, Any]]:
    """Generate mock calendar events within a time window.

    Returns fixed events from FIXED_EVENTS_2026_02, filtered by the requested time range
    and optionally by keywords.
    """
    filtered_events = []

    for event in FIXED_EVENTS_2026_02:
        # Parse the event's start time from the ISO string
        event_start_str = event["start"]["dateTime"]
        # Handle both "Z" (UTC) and timezone offset formats
        if event_start_str.endswith("Z"):
            event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
        else:
            event_start = datetime.fromisoformat(event_start_str)

        # Check if event falls within the requested time range
        # Normalize both to UTC for comparison if needed, or compare directly if both are timezone-aware
        if start_time <= event_start < end_time:
            # If keywords are provided, filter by matching summaries
            if keywords:
                event_summary_lower = event["summary"].lower()
                event_description_lower = event.get("description", "").lower()
                # Check if any keyword matches in summary or description
                if any(kw.lower() in event_summary_lower or kw.lower() in event_description_lower for kw in keywords):
                    filtered_events.append(event)
            else:
                filtered_events.append(event)

    # Sort by start time to ensure consistent ordering
    filtered_events.sort(key=lambda e: e["start"]["dateTime"])

    # Return up to 'count' events (or all if fewer than count)
    return filtered_events[:count] if count else filtered_events
