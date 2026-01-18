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
    """Generate a relative dates cheat sheet.
    
    Args:
        current_datetime: Timezone-aware datetime object
        timezone: IANA timezone string (e.g., "America/Los_Angeles")
    
    Returns:
        Formatted string with relative date expressions mapped to dates
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
    current_hour = current_datetime.hour
    is_early_morning = current_hour < 4
    
    items = []
    items.append("RELATIVE DATES CHEAT SHEET:")
    
    # Get timezone offset for ISO string formatting
    offset = current_datetime.strftime("%z")
    if offset:
        # Format offset as -08:00 instead of -0800
        offset_formatted = f"{offset[:3]}:{offset[3:]}"
    else:
        offset_formatted = "+00:00"
    
    # Helper function to format date
    def format_date(d: datetime.date) -> str:
        weekday_abbr = calendar.day_abbr[d.weekday()]
        return f"{weekday_abbr} {d.month}/{d.day}/{str(d.year)[-2:]}"
    
    # Helper function to format date range as ISO strings
    def format_date_range(start_date: datetime.date, end_date: datetime.date) -> str:
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz)
        end_time = datetime.strptime("23:59:59", "%H:%M:%S").time()
        end_dt = datetime.combine(end_date, end_time).replace(tzinfo=tz)
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()
        return f"({start_iso} to {end_iso})"
    
    # Helper function to format single day range
    def format_day_range(d: datetime.date) -> str:
        return format_date_range(d, d)
    
    # Today
    items.append(f'- "today": {format_date(today)} {format_day_range(today)}')
    
    # Tomorrow
    if is_early_morning:
        tomorrow_date = today  # Later today after they sleep
        tomorrow_note = f" (NOTE: Since it is super early ({current_hour}:00 AM), tomorrow likely means later today after they sleep, not the next calendar day)"
    else:
        tomorrow_date = today + timedelta(days=1)
        tomorrow_note = ""
    items.append(f'- "tomorrow": {format_date(tomorrow_date)} {format_day_range(tomorrow_date)}{tomorrow_note}')
    
    # Day after tomorrow
    if is_early_morning:
        day_after_date = today + timedelta(days=1)  # Tomorrow after they sleep two nights
        day_after_note = f" (NOTE: Since it is super early ({current_hour}:00 AM), day after tomorrow likely means tomorrow after they sleep two nights, not two calendar days from now)"
    else:
        day_after_date = today + timedelta(days=2)
        day_after_note = ""
    items.append(f'- "day after tomorrow" / "day after next": {format_date(day_after_date)} {format_day_range(day_after_date)}{day_after_note}')
    
    # Days of week (next occurrence)
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, day_name in enumerate(weekday_names):
        # Find next occurrence of this weekday
        days_ahead = (i - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week's occurrence
        next_date = today + timedelta(days=days_ahead)
        items.append(f'- "{day_name}": {format_date(next_date)} {format_day_range(next_date)}')
    
    # Next [day] (that weekday of next week)
    for i, day_name in enumerate(weekday_names):
        # Find this weekday of next week
        days_ahead = (i - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        # Add 7 more days to get next week's occurrence
        next_week_date = today + timedelta(days=days_ahead + 7)
        items.append(f'- "next {day_name}": {format_date(next_week_date)} {format_day_range(next_week_date)}')
    
    # This week (Monday to Sunday)
    # If it's Saturday or Sunday, "this week" means the week starting on the upcoming Monday
    # Otherwise, it's the current week
    days_since_monday = today.weekday()
    if today.weekday() >= 5:  # Saturday (5) or Sunday (6)
        # On weekend, "this week" refers to the week starting on the upcoming Monday
        days_until_monday = (7 - days_since_monday) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # Next Monday
        week_start = today + timedelta(days=days_until_monday)
    else:
        # On weekdays, "this week" is the current week
        week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    items.append(f'- "this week": {format_date(week_start)} - {format_date(week_end)} {format_date_range(week_start, week_end)}')
    
    # Next week
    # If it's Saturday or Sunday, "next week" is the week after the upcoming week
    # Otherwise, it's the week after the current week
    next_week_start = week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)
    items.append(f'- "next week": {format_date(next_week_start)} - {format_date(next_week_end)} {format_date_range(next_week_start, next_week_end)}')
    
    # Week after next
    week_after_next_start = week_start + timedelta(days=14)
    week_after_next_end = week_after_next_start + timedelta(days=6)
    items.append(f'- "week after next": {format_date(week_after_next_start)} - {format_date(week_after_next_end)} {format_date_range(week_after_next_start, week_after_next_end)}')
    
    # This weekend (Saturday-Sunday)
    # Find the next Saturday from today
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        # Today is Saturday, use this weekend
        this_weekend_sat = today
    else:
        # Find next Saturday
        this_weekend_sat = today + timedelta(days=days_until_saturday)
    this_weekend_sun = this_weekend_sat + timedelta(days=1)
    items.append(f'- "this weekend": {format_date(this_weekend_sat)} - {format_date(this_weekend_sun)} {format_date_range(this_weekend_sat, this_weekend_sun)}')
    
    # Next weekend
    next_weekend_sat = this_weekend_sat + timedelta(days=7)
    next_weekend_sun = next_weekend_sat + timedelta(days=1)
    items.append(f'- "next weekend": {format_date(next_weekend_sat)} - {format_date(next_weekend_sun)} {format_date_range(next_weekend_sat, next_weekend_sun)}')
    
    # This month
    month_name = calendar.month_name[current_datetime.month]
    month_start = datetime(current_datetime.year, current_datetime.month, 1, tzinfo=tz).date()
    # Get last day of month
    if current_datetime.month == 12:
        month_end = datetime(current_datetime.year + 1, 1, 1, tzinfo=tz).date() - timedelta(days=1)
    else:
        month_end = datetime(current_datetime.year, current_datetime.month + 1, 1, tzinfo=tz).date() - timedelta(days=1)
    items.append(f'- "this month": {month_name} {current_datetime.year} {format_date_range(month_start, month_end)}')
    
    # Next month
    if current_datetime.month == 12:
        next_month = 1
        next_year = current_datetime.year + 1
    else:
        next_month = current_datetime.month + 1
        next_year = current_datetime.year
    next_month_name = calendar.month_name[next_month]
    next_month_start = datetime(next_year, next_month, 1, tzinfo=tz).date()
    # Get last day of next month
    if next_month == 12:
        next_month_end = datetime(next_year + 1, 1, 1, tzinfo=tz).date() - timedelta(days=1)
    else:
        next_month_end = datetime(next_year, next_month + 1, 1, tzinfo=tz).date() - timedelta(days=1)
    items.append(f'- "next month": {next_month_name} {next_year} {format_date_range(next_month_start, next_month_end)}')
    
    return "\n".join(items)


def generate_time_reference(current_datetime: datetime, timezone: str) -> str:
    """Generate time reference including calendar view and relative dates cheat sheet.
    
    Args:
        current_datetime: Timezone-aware datetime object
        timezone: IANA timezone string (e.g., "America/Los_Angeles")
    
    Returns:
        Formatted string containing calendar view and relative dates cheat sheet
    """
    calendar_view = _build_calendar_view(current_datetime, timezone)
    cheat_sheet = _build_relative_dates_cheat_sheet(current_datetime, timezone)
    
    return f"{cheat_sheet}"