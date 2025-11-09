"""Background service for emitting calendar events based on user preferences."""

import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.async_agent import JobType, async_agent_service
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class CalendarEventEmitter:
    """
    Background service that emits calendar events based on user preferences.

    This service:
    1. Reads calendar_preferences (gym, sleep, focus blocks, etc.)
    2. Checks if events need to be created/updated
    3. Creates async jobs to add events to calendars
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    def get_active_preferences(
        self, user_id: UUID | str, preference_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active calendar preferences for a user.

        Args:
            user_id: User ID
            preference_type: Filter by type (optional)

        Returns:
            List of preference dictionaries
        """
        try:
            query = (
                self.supabase.table("calendar_preferences")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("is_active", True)
                .eq("auto_schedule", True)
            )

            if preference_type:
                query = query.eq("preference_type", preference_type)

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get active preferences: {e}", exc_info=True)
            return []

    def should_emit_event(
        self, preference: Dict[str, Any], current_time: datetime
    ) -> bool:
        """
        Determine if an event should be emitted for this preference.

        Args:
            preference: Preference dictionary
            current_time: Current datetime

        Returns:
            True if event should be emitted
        """
        # Check if preference applies to today
        day_of_week = current_time.weekday() + 1  # 1=Mon, 7=Sun
        days = preference.get("day_of_week")

        if days and len(days) > 0:
            if day_of_week not in days:
                return False

        # Check if event already exists for this time period
        # (This would require checking Google Calendar - simplified for now)
        return True

    def emit_preference_events(
        self, user_id: UUID | str, start_date: datetime, end_date: datetime
    ) -> List[str]:
        """
        Emit calendar events for all active preferences in a date range.

        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of job IDs created
        """
        preferences = self.get_active_preferences(user_id)
        job_ids = []

        current_date = start_date.date()
        end_date_only = end_date.date()

        while current_date <= end_date_only:
            current_datetime = datetime.combine(current_date, dt_time.min)

            for preference in preferences:
                if self.should_emit_event(preference, current_datetime):
                    # Calculate event start time
                    start_time_str = preference["start_time"]
                    if isinstance(start_time_str, str):
                        # Parse time string (HH:MM:SS or HH:MM)
                        time_parts = start_time_str.split(":")
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        event_start = datetime.combine(current_date, dt_time(hour, minute))
                    else:
                        # Assume it's already a time object
                        event_start = datetime.combine(current_date, start_time_str)

                    event_end = event_start + timedelta(minutes=preference["duration_minutes"])

                    # Create async job to add event
                    job_id = async_agent_service.create_job(
                        user_id=user_id,
                        job_type=JobType.CALENDAR_SYNC,
                        payload={
                            "operation": "create_preference_event",
                            "preference_id": preference["id"],
                            "title": preference["title"],
                            "description": preference.get("description"),
                            "start_time": event_start.isoformat(),
                            "end_time": event_end.isoformat(),
                            "calendar_id": preference.get("calendar_id"),
                            "buffer_before": preference.get("buffer_before_minutes", 0),
                            "buffer_after": preference.get("buffer_after_minutes", 0),
                        },
                        agent_action="create",
                        priority=preference.get("priority", 5),
                    )

                    job_ids.append(job_id)
                    logger.info(
                        f"Queued preference event job {job_id} for user {user_id}: "
                        f"{preference['title']} on {current_date}"
                    )

            current_date += timedelta(days=1)

        return job_ids

    def process_user_preferences(self, user_id: UUID | str, days_ahead: int = 7) -> int:
        """
        Process and emit events for a user's preferences.

        Args:
            user_id: User ID
            days_ahead: Number of days ahead to schedule

        Returns:
            Number of jobs created
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)

        job_ids = self.emit_preference_events(user_id, start_date, end_date)
        logger.info(f"Created {len(job_ids)} preference event jobs for user {user_id}")

        return len(job_ids)


# Singleton instance
calendar_event_emitter = CalendarEventEmitter()

