"""Service for managing user insights discovered by the LLM agent."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from models.user_insights import UserInsightCreate, UserInsightUpdate
from services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class UserInsightsService:
    """Service for managing LLM-discovered user insights."""

    def __init__(self):
        self.supabase = get_supabase_client()

    def create_insight(
        self,
        user_id: UUID | str,
        insight_type: str,
        category: str,
        key: str,
        value: Dict[str, Any],
        confidence: float = 0.5,
        source: str = "agent",
        source_request_id: Optional[UUID | str] = None,
    ) -> str:
        """
        Create or update a user insight (upsert based on user_id, category, key).

        Args:
            user_id: User ID
            insight_type: Type ('preference', 'habit', 'pattern', 'goal', 'constraint')
            category: Category ('schedule', 'meetings', 'health', 'work', 'personal')
            key: Unique key within category
            value: JSONB value for the insight
            confidence: LLM confidence (0.0 to 1.0)
            source: Source ('agent', 'pattern_analysis', 'explicit')
            source_request_id: ID of request that generated this insight

        Returns:
            Insight ID
        """
        try:
            insight_data = UserInsightCreate(
                user_id=str(user_id),
                insight_type=insight_type,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                source=source,
                source_request_id=str(source_request_id) if source_request_id else None,
            )

            # Upsert: insert or update if exists
            result = (
                self.supabase.table("user_insights")
                .upsert(
                    insight_data.model_dump(exclude_none=True),
                    on_conflict="user_id,category,key",
                )
                .execute()
            )

            if result.data:
                insight_id = result.data[0]["id"]
                logger.info(
                    f"Created/updated insight {insight_id} for user {user_id}: {category}/{key}"
                )
                return insight_id
            else:
                raise ValueError("Failed to create insight")

        except Exception as e:
            logger.error(f"Failed to create insight: {e}", exc_info=True)
            raise

    def get_user_insights(
        self,
        user_id: UUID | str,
        category: Optional[str] = None,
        insight_type: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        """
        Get user insights, optionally filtered by category or type.

        Args:
            user_id: User ID
            category: Filter by category (optional)
            insight_type: Filter by type (optional)

        Returns:
            List of insight dictionaries
        """
        try:
            query = self.supabase.table("user_insights").select("*").eq("user_id", str(user_id))

            if category:
                query = query.eq("category", category)

            if insight_type:
                query = query.eq("insight_type", insight_type)

            result = query.order("updated_at", desc=True).execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get user insights: {e}", exc_info=True)
            return []

    def update_insight(
        self,
        insight_id: UUID | str,
        value: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
    ) -> None:
        """
        Update an existing insight.

        Args:
            insight_id: Insight ID
            value: New value (optional)
            confidence: New confidence (optional)
        """
        try:
            update_data = UserInsightUpdate(value=value, confidence=confidence)
            self.supabase.table("user_insights").update(
                update_data.model_dump(exclude_none=True)
            ).eq("id", str(insight_id)).execute()

            logger.info(f"Updated insight {insight_id}")

        except Exception as e:
            logger.error(f"Failed to update insight: {e}", exc_info=True)
            raise


# Singleton instance
user_insights_service = UserInsightsService()

