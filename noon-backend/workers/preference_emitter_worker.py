"""Background worker for emitting calendar preference events."""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.calendar_event_emitter import calendar_event_emitter
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class PreferenceEmitterWorker:
    """Background worker that periodically emits calendar events from preferences."""

    def __init__(self, poll_interval_seconds: int = 300):  # 5 minutes default
        """
        Initialize the preference emitter worker.

        Args:
            poll_interval_seconds: How often to check for users to process
        """
        self.poll_interval = poll_interval_seconds
        self.supabase = get_supabase_client()
        self.running = False

    async def run(self):
        """Run the worker loop."""
        self.running = True
        logger.info("Preference emitter worker started")

        while self.running:
            try:
                await self.process_all_users()
            except Exception as e:
                logger.exception("Error in preference emitter worker loop: %s", e)

            await asyncio.sleep(self.poll_interval)

    async def process_all_users(self):
        """Process preferences for all active users."""
        try:
            # Get all users (simplified - in production, you might want to filter)
            result = self.supabase.table("users").select("id").execute()
            users = result.data or []

            logger.info(f"Processing preferences for {len(users)} users")

            for user in users:
                try:
                    user_id = user["id"]
                    # Process preferences for next 7 days (run in executor to avoid blocking)
                    job_count = await asyncio.get_event_loop().run_in_executor(
                        None,
                        calendar_event_emitter.process_user_preferences,
                        user_id,
                        7,  # days_ahead
                    )
                    if job_count > 0:
                        logger.info(
                            f"Created {job_count} preference event jobs for user {user_id}"
                        )
                except Exception as e:
                    logger.error(f"Failed to process preferences for user {user_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to get users: {e}", exc_info=True)

    def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("Preference emitter worker stopped")


async def main():
    """Main entry point for the worker."""
    worker = PreferenceEmitterWorker(poll_interval_seconds=300)  # 5 minutes
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        worker.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())

