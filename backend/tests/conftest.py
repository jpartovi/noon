"""Pytest fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set required env vars for tests
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")

from main import app


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_authenticated_user():
    """Mock authenticated user data."""
    return {
        "id": "test-user-123",
        "phone": "+1234567890",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def auth_headers():
    """Mock valid authentication headers."""
    return {"Authorization": "Bearer test-token-123"}


@pytest.fixture
def mock_google_account():
    """Mock Google account with tokens."""
    return {
        "id": "google-account-123",
        "email": "test@example.com",
        "tokens": {
            "access_token": "ya29.test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_at": "2024-12-31T23:59:59Z",
            "token_type": "Bearer",
        },
    }


@pytest.fixture
def mock_get_current_user(mock_authenticated_user):
    """Mock the get_current_user dependency."""
    from dependencies import get_current_user
    from schemas.user import AuthenticatedUser

    def override_get_current_user():
        return AuthenticatedUser(**mock_authenticated_user)

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_list_google_accounts():
    """Mock list_google_accounts function."""
    with patch("agent.routes.agent.supabase_client.list_google_accounts") as mock:
        mock.return_value = [
            {
                "id": "google-account-123",
                "email": "test@example.com",
                "access_token": "ya29.test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_at": "2024-12-31T23:59:59Z",
            }
        ]
        yield mock


@pytest.fixture
def mock_transcription_service():
    """Mock transcription service."""
    with patch("agent.routes.agent.transcription_service.transcribe") as mock:

        async def mock_transcribe(*args, **kwargs):
            return "What am I doing next weekend?"

        mock.side_effect = mock_transcribe
        yield mock


@pytest.fixture
def mock_agent_graph():
    """Mock agent graph invocation."""
    with patch("agent.routes.agent.noon_graph.invoke") as mock_invoke:
        # Mock invoke method to return agent response
        def mock_invoke_fn(input_state):
            return {
                "success": True,
                "request": "show-schedule",
                "metadata": {"start-date": "2024-11-16", "end-date": "2024-11-17"},
            }

        mock_invoke.side_effect = mock_invoke_fn
        yield mock_invoke
