"""Background worker for processing async agent jobs."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.async_agent import async_agent_service, JobType
from services.calendar_event_emitter import calendar_event_emitter
from services.user_insights import user_insights_service

logger = logging.getLogger(__name__)


class AsyncJobProcessor:
    """Background worker that processes async agent jobs."""

    def __init__(self, poll_interval_seconds: int = 5):
        """
        Initialize the async job processor.

        Args:
            poll_interval_seconds: How often to poll for new jobs
        """
        self.poll_interval = poll_interval_seconds
        self.running = False

    async def run(self):
        """Run the worker loop."""
        self.running = True
        logger.info("Async job processor started")

        while self.running:
            try:
                await self.process_pending_jobs()
            except Exception as e:
                logger.exception("Error in async job processor loop: %s", e)

            await asyncio.sleep(self.poll_interval)

    async def process_pending_jobs(self):
        """Process pending jobs from the queue."""
        jobs = async_agent_service.get_pending_jobs(limit=10)

        for job in jobs:
            try:
                # Mark as running
                async_agent_service.update_job_status(job["id"], "running")

                # Process based on job type (run in executor to avoid blocking)
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._process_job, job
                )

                # Mark as completed
                async_agent_service.update_job_status(
                    job["id"], "completed", result=result
                )

            except Exception as e:
                logger.exception(f"Error processing job {job['id']}: {e}")

                # Retry or mark as failed
                if job["retry_count"] < job["max_retries"]:
                    async_agent_service.retry_job(job["id"])
                else:
                    async_agent_service.update_job_status(
                        job["id"], "failed", error_message=str(e)
                    )

    def _process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single job based on its type."""
        job_type = job["job_type"]
        payload = job.get("payload", {})
        user_id = job["user_id"]

        if job_type == JobType.UPDATE_INSIGHT or job_type == JobType.PATTERN_ANALYSIS:
            # Check if this is an insight update operation
            operation = payload.get("operation")
            if operation == "update_insight":
                # Update user insight
                user_insights_service.create_insight(
                    user_id=user_id,
                    insight_type=payload["insight_type"],
                    category=payload["category"],
                    key=payload["key"],
                    value=payload["value"],
                    confidence=payload.get("confidence", 0.5),
                    source_request_id=payload.get("source_request_id"),
                )
                return {"status": "success", "message": "Insight updated"}

        elif job_type == JobType.EMIT_PREFERENCE_EVENTS:
            # Emit calendar preference events
            days_ahead = payload.get("days_ahead", 7)
            job_count = calendar_event_emitter.process_user_preferences(
                user_id, days_ahead=days_ahead
            )
            return {"status": "success", "jobs_created": job_count}

        elif job_type == JobType.CALENDAR_SYNC:
            # Handle calendar sync operations
            operation = payload.get("operation")
            if operation == "create_preference_event":
                # This would create an event in Google Calendar
                # For now, return success - actual implementation would call gcal_wrapper
                return {
                    "status": "success",
                    "message": "Preference event creation queued",
                }

        # Default: return success
        return {"status": "success", "message": f"Processed {job_type}"}

    def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info("Async job processor stopped")


async def main():
    """Main entry point for the worker."""
    processor = AsyncJobProcessor(poll_interval_seconds=5)
    try:
        await processor.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        processor.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())

