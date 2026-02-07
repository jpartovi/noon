"""Time reference generation for agent system prompts.

This module provides functions to generate calendar views and relative date
cheat sheets for inclusion in agent system prompts.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import calendar


def _build_calendar_view(current_datetime: datetime, timezone: str) -> str:
    """Generate a multi-week Gregorian calendar view.
    
    Args:
        current_datetime: Timezone-aware datetime object
        timezone: IANA timezone string (e.g., "America/Los_Angeles")
    
    Returns:
        Formatted string showing calendar grid with today's date marked
    """
    # Ensure we're working in the user's timezone
    if current_datetime.tzinfo is None:
        tz = ZoneInfo(timezone)
        current_datetime = current_datetime.replace(tzinfo=tz)
    else:
        # Convert to user's timezone if needed
        tz = ZoneInfo(timezone)
        current_datetime = current_datetime.astimezone(tz)
    
    today = current_datetime.date()
    
    # Start from the Monday of the week containing today
    days_since_monday = today.weekday()  # Monday is 0
    calendar_start = today - timedelta(days=days_since_monday)
    
    # Generate 6 weeks of calendar
    lines = []
    lines.append("CALENDAR VIEW:")
    lines.append("Mon  Tue  Wed  Thu  Fri  Sat  Sun")
    
    current_date = calendar_start
    for week in range(6):
        week_days = []
        for day in range(7):
            # Format day as M/D (e.g., 1/17, 1/18)
            day_str = f"{current_date.month}/{current_date.day}"
            
            # Mark today with asterisk
            if current_date == today:
                day_str = f"{current_date.month}/{current_date.day}*"
            
            week_days.append(day_str)
            current_date += timedelta(days=1)
        
        lines.append("  ".join(week_days))
    
    lines.append("")
    lines.append("(* = today)")
    
    return "\n".join(lines)


def _build_relative_dates_cheat_sheet(current_datetime: datetime, timezone: str) -> str:
    """Generate a compact relative dates cheat sheet.

    Args:
        current_datetime: Timezone-aware datetime object
        timezone: IANA timezone string (e.g., "America/Los_Angeles")

    Returns:
        Formatted string with relative date expressions mapped to dates (compact format)
    """
    # Ensure we're working in the user's timezone
    if current_datetime.tzinfo is None:
        tz = ZoneInfo(timezone)
        current_datetime = current_datetime.replace(tzinfo=tz)
    else:
        tz = ZoneInfo(timezone)
        current_datetime = current_datetime.astimezone(tz)

    today = current_datetime.date()
    current_hour = current_datetime.hour
    is_early_morning = current_hour < 4
    is_weekday = today.weekday() < 5

    # Helper to format date compactly
    def fmt(d) -> str:
        return f"{calendar.day_abbr[d.weekday()]} {d.month}/{d.day}"

    lines = ["DATES:"]

    # Today and tomorrow
    lines.append(f"today={fmt(today)}")
    tomorrow = today if is_early_morning else today + timedelta(days=1)
    lines.append(f"tomorrow={fmt(tomorrow)}")

    # Days of week (next occurrence, 1-7 days ahead)
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days_line = []
    for i, name in enumerate(weekday_names):
        days_ahead = (i - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        d = today + timedelta(days=days_ahead)
        days_line.append(f"{name}={d.month}/{d.day}")
    lines.append(" ".join(days_line))

    # Calculate week/weekend boundaries
    if is_weekday:
        days_since_monday = today.weekday()
        this_week_start = today - timedelta(days=days_since_monday)
        this_week_end = this_week_start + timedelta(days=4)
        days_until_saturday = (5 - today.weekday()) % 7 or 7
        this_weekend_sat = today + timedelta(days=days_until_saturday)
    else:
        days_until_monday = (7 - today.weekday()) % 7 or 7
        this_week_start = today + timedelta(days=days_until_monday)
        this_week_end = this_week_start + timedelta(days=4)
        this_weekend_sat = today if today.weekday() == 5 else today - timedelta(days=1)

    this_weekend_sun = this_weekend_sat + timedelta(days=1)
    next_week_start = this_week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=4)
    next_weekend_sat = this_weekend_sat + timedelta(days=7)
    next_weekend_sun = next_weekend_sat + timedelta(days=1)

    lines.append(f"this_week={fmt(this_week_start)}-{fmt(this_week_end)}")
    lines.append(f"this_weekend={fmt(this_weekend_sat)}-{fmt(this_weekend_sun)}")
    lines.append(f"next_week={fmt(next_week_start)}-{fmt(next_week_end)}")
    lines.append(f"next_weekend={fmt(next_weekend_sat)}-{fmt(next_weekend_sun)}")

    # "next X" for each weekday
    next_days = []
    for i, name in enumerate(weekday_names):
        if i < 5:
            d = next_week_start + timedelta(days=i)
        else:
            d = next_weekend_sat if i == 5 else next_weekend_sun
        next_days.append(f"next_{name}={d.month}/{d.day}")
    lines.append(" ".join(next_days))

    return "\n".join(lines)


def generate_time_reference(current_datetime: datetime, timezone: str) -> str:
    """Generate time reference including relative dates cheat sheet.

    Args:
        current_datetime: Timezone-aware datetime object
        timezone: IANA timezone string (e.g., "America/Los_Angeles")

    Returns:
        Formatted string containing relative dates cheat sheet
    """
    cheat_sheet = _build_relative_dates_cheat_sheet(current_datetime, timezone)

    return cheat_sheet