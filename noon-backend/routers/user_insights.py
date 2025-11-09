"""Router for agent to update user insights asynchronously."""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import AuthenticatedUser, get_current_user
from services.async_agent import JobType, async_agent_service
from services.user_insights import user_insights_service

router = APIRouter(prefix="/user-insights", tags=["user-insights"])
logger = logging.getLogger(__name__)


@router.post("/update")
async def update_user_insight_async(
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Async endpoint for agent to update user insights.

    This endpoint is designed to be called by the LangGraph agent when it discovers
    something insightful about the user. The update is performed asynchronously.

    Request body:
    {
        "insight_type": "preference" | "habit" | "pattern" | "goal" | "constraint",
        "category": "schedule" | "meetings" | "health" | "work" | "personal",
        "key": "unique_key_within_category",
        "value": {...},  // JSONB value
        "confidence": 0.0-1.0,
        "source_request_id": "uuid"  // Optional: ID of request that generated this
    }

    Returns:
        {"job_id": "...", "status": "queued"}
    """
    try:
        # Validate required fields
        required_fields = ["insight_type", "category", "key", "value"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        # Create async job to update insight
        job_id = async_agent_service.create_job(
            user_id=current_user.id,
            job_type=JobType.PATTERN_ANALYSIS,  # Using pattern_analysis for insight updates
            payload={
                "operation": "update_insight",
                "insight_type": payload["insight_type"],
                "category": payload["category"],
                "key": payload["key"],
                "value": payload["value"],
                "confidence": payload.get("confidence", 0.5),
                "source_request_id": payload.get("source_request_id"),
            },
            priority=3,  # High priority for user insights
        )

        logger.info(
            f"Queued insight update job {job_id} for user {current_user.id}: "
            f"{payload['category']}/{payload['key']}"
        )

        return {"job_id": job_id, "status": "queued"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to queue insight update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue insight update: {str(e)}",
        ) from e

