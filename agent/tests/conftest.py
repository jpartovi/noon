"""Test fixtures for agent benchmark tests."""

# Load .env file BEFORE any other imports that might need API keys
from dotenv import load_dotenv
from pathlib import Path

# Load from project root .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

import pytest
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from unittest.mock import patch
from dataclasses import dataclass, field

from agent.mock_client import MockClient
from agent.tools import set_calendar_client


@dataclass
class BenchmarkMetrics:
    """Captures LLM call count and timing for benchmarks."""

    llm_call_count: int = 0
    llm_durations: List[float] = field(default_factory=list)
    total_start_time: Optional[float] = None
    total_end_time: Optional[float] = None

    def start(self):
        """Start timing."""
        self.total_start_time = time.time()
        self.llm_call_count = 0
        self.llm_durations = []

    def record_llm_call(self, duration: float):
        """Record an LLM call."""
        self.llm_call_count += 1
        self.llm_durations.append(duration)

    def stop(self):
        """Stop timing."""
        self.total_end_time = time.time()

    @property
    def total_duration(self) -> float:
        """Total execution time."""
        if self.total_start_time and self.total_end_time:
            return self.total_end_time - self.total_start_time
        return 0.0

    @property
    def total_llm_duration(self) -> float:
        """Sum of all LLM call durations."""
        return sum(self.llm_durations)


@pytest.fixture
def mock_client():
    """Set up MockClient for calendar operations."""
    client = MockClient()
    set_calendar_client(client)
    yield client
    # Reset to None after test
    set_calendar_client(None)


@pytest.fixture
def metrics():
    """Provide benchmark metrics collector."""
    return BenchmarkMetrics()


@pytest.fixture
def test_timezone():
    """Standard test timezone."""
    return "America/Los_Angeles"


@pytest.fixture
def test_current_time(test_timezone):
    """Current time for tests - Monday at 10am."""
    tz = ZoneInfo(test_timezone)
    # Use a fixed date that's a Monday
    dt = datetime(2026, 2, 9, 10, 0, 0, tzinfo=tz)  # Monday, Feb 9, 2026
    return dt


@pytest.fixture
def test_input_state(test_timezone, test_current_time) -> Dict[str, Any]:
    """Base input state with auth, timezone, and time context."""
    # Pre-fetch writable calendars for validation (avoids extra list_calendars calls)
    from agent.mocks import generate_mock_calendars

    return {
        "auth": {
            "access_token": "test-token-12345",
            "refresh_token": "test-refresh-token",
            "user_id": "test-user-id",
        },
        "timezone": test_timezone,
        "current_time": test_current_time.isoformat(),
        "current_day_of_week": test_current_time.strftime("%A"),
        "messages": [],
        "tool_results": {},
        "success": True,
        "terminated": False,
        "type": None,
        "metadata": {},
        "message": None,
        "writable_calendars": generate_mock_calendars(),  # Pre-fetched for validation
    }


def create_test_state(query: str, base_state: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test state with the given query."""
    state = base_state.copy()
    state["query"] = query
    return state
