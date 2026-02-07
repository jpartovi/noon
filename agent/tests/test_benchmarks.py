"""Performance benchmark tests for Noon Agent.

These tests simulate real user queries and measure:
- Agent response type correctness
- LLM call count (for optimization verification)
- Total execution time

Run with: uv run pytest tests/test_benchmarks.py -v

Note: Requires OPENAI_API_KEY environment variable to be set.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from agent.main import noon_graph
from tests.conftest import create_test_state, BenchmarkMetrics


# ============================================================================
# LLM Call Instrumentation
# ============================================================================


class InstrumentedLLM:
    """Wrapper around LLM that counts invocations."""

    def __init__(self, llm, metrics: BenchmarkMetrics):
        self._llm = llm
        self._metrics = metrics

    def invoke(self, *args, **kwargs):
        start = time.time()
        result = self._llm.invoke(*args, **kwargs)
        duration = time.time() - start
        self._metrics.record_llm_call(duration)
        return result

    def __getattr__(self, name):
        return getattr(self._llm, name)


class LLMCallCounter:
    """Context manager to count LLM invocations."""

    def __init__(self, metrics: BenchmarkMetrics):
        self.metrics = metrics
        self._original_llm = None

    def __enter__(self):
        import agent.main

        self._original_llm = agent.main.llm_with_tools
        self.metrics.start()

        # Replace with instrumented wrapper
        agent.main.llm_with_tools = InstrumentedLLM(self._original_llm, self.metrics)
        return self

    def __exit__(self, *args):
        import agent.main

        agent.main.llm_with_tools = self._original_llm
        self.metrics.stop()


# ============================================================================
# Show Schedule Tests (1 LLM call expected)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "what's on my calendar today",
        "show me my schedule for tomorrow",
        "what do I have this week",
        "what's my schedule on Friday",
    ],
)
async def test_show_schedule_queries(
    query: str, mock_client, metrics: BenchmarkMetrics, test_input_state: Dict[str, Any]
):
    """Test show schedule queries complete with expected LLM call count."""
    max_llm_calls = 1
    expected_type = "show-schedule"

    state = create_test_state(query, test_input_state)
    graph = noon_graph

    with LLMCallCounter(metrics):
        result = await graph.ainvoke(state)

    # Print metrics for comparison
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  Expected type: {expected_type}")
    print(f"  Actual type: {result.get('type')}")
    print(f"  LLM calls: {metrics.llm_call_count} (max: {max_llm_calls})")
    print(f"  Total time: {metrics.total_duration:.2f}s")
    print(f"  LLM time: {metrics.total_llm_duration:.2f}s")
    print(f"{'='*60}")

    assert result.get("type") == expected_type, f"Expected {expected_type}, got {result.get('type')}"
    assert (
        metrics.llm_call_count <= max_llm_calls
    ), f"Expected <= {max_llm_calls} LLM calls, got {metrics.llm_call_count}"


# ============================================================================
# Show Event Tests (2 LLM calls expected: search + show)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "when is my doctor appointment",
        "what time is my dinner tomorrow",
        "when is the team meeting",
        "find my haircut appointment",
    ],
)
async def test_show_event_queries(
    query: str, mock_client, metrics: BenchmarkMetrics, test_input_state: Dict[str, Any]
):
    """Test show event queries complete with expected LLM call count."""
    max_llm_calls = 2
    expected_type = "show-event"

    state = create_test_state(query, test_input_state)
    graph = noon_graph

    with LLMCallCounter(metrics):
        result = await graph.ainvoke(state)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  Expected type: {expected_type}")
    print(f"  Actual type: {result.get('type')}")
    print(f"  LLM calls: {metrics.llm_call_count} (max: {max_llm_calls})")
    print(f"  Total time: {metrics.total_duration:.2f}s")
    print(f"  LLM time: {metrics.total_llm_duration:.2f}s")
    print(f"{'='*60}")

    assert result.get("type") == expected_type, f"Expected {expected_type}, got {result.get('type')}"
    assert (
        metrics.llm_call_count <= max_llm_calls
    ), f"Expected <= {max_llm_calls} LLM calls, got {metrics.llm_call_count}"


# ============================================================================
# Create Event Tests (2 LLM calls expected with calendar prefetch optimization)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "schedule a meeting tomorrow at 3pm",
        "add lunch with Sarah on Friday at noon",
        "put dentist appointment next Tuesday at 2pm",
        "create a reminder for mom's birthday on March 5th",
    ],
)
async def test_create_event_queries(
    query: str, mock_client, metrics: BenchmarkMetrics, test_input_state: Dict[str, Any]
):
    """Test create event queries complete with expected LLM call count.

    With calendar prefetch optimization, create events should complete in 2 LLM calls:
    1. list_calendars (prefetched) + request_create_event
    2. (validation retry if needed)
    """
    max_llm_calls = 2
    expected_type = "create-event"

    state = create_test_state(query, test_input_state)
    graph = noon_graph

    with LLMCallCounter(metrics):
        result = await graph.ainvoke(state)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  Expected type: {expected_type}")
    print(f"  Actual type: {result.get('type')}")
    print(f"  LLM calls: {metrics.llm_call_count} (max: {max_llm_calls})")
    print(f"  Total time: {metrics.total_duration:.2f}s")
    print(f"  LLM time: {metrics.total_llm_duration:.2f}s")
    print(f"{'='*60}")

    assert result.get("type") == expected_type, f"Expected {expected_type}, got {result.get('type')}"
    assert (
        metrics.llm_call_count <= max_llm_calls
    ), f"Expected <= {max_llm_calls} LLM calls, got {metrics.llm_call_count}"


# ============================================================================
# Update Event Tests (2 LLM calls expected)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "move my doctor appointment to Thursday",
        "change the team meeting to 4pm",
        "reschedule my lunch to 1pm",
    ],
)
async def test_update_event_queries(
    query: str, mock_client, metrics: BenchmarkMetrics, test_input_state: Dict[str, Any]
):
    """Test update event queries complete with expected LLM call count."""
    max_llm_calls = 3  # Allow retry if initial search misses
    expected_type = "update-event"

    state = create_test_state(query, test_input_state)
    graph = noon_graph

    with LLMCallCounter(metrics):
        result = await graph.ainvoke(state)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  Expected type: {expected_type}")
    print(f"  Actual type: {result.get('type')}")
    print(f"  LLM calls: {metrics.llm_call_count} (max: {max_llm_calls})")
    print(f"  Total time: {metrics.total_duration:.2f}s")
    print(f"  LLM time: {metrics.total_llm_duration:.2f}s")
    print(f"{'='*60}")

    assert result.get("type") == expected_type, f"Expected {expected_type}, got {result.get('type')}"
    assert (
        metrics.llm_call_count <= max_llm_calls
    ), f"Expected <= {max_llm_calls} LLM calls, got {metrics.llm_call_count}"


# ============================================================================
# Delete Event Tests (2 LLM calls expected)
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "cancel my 3pm meeting",
        "delete the doctor appointment",
        "remove the coffee with Sarah",
    ],
)
async def test_delete_event_queries(
    query: str, mock_client, metrics: BenchmarkMetrics, test_input_state: Dict[str, Any]
):
    """Test delete event queries complete with expected LLM call count."""
    max_llm_calls = 3  # Allow retry if initial search misses
    expected_type = "delete-event"

    state = create_test_state(query, test_input_state)
    graph = noon_graph

    with LLMCallCounter(metrics):
        result = await graph.ainvoke(state)

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"  Expected type: {expected_type}")
    print(f"  Actual type: {result.get('type')}")
    print(f"  LLM calls: {metrics.llm_call_count} (max: {max_llm_calls})")
    print(f"  Total time: {metrics.total_duration:.2f}s")
    print(f"  LLM time: {metrics.total_llm_duration:.2f}s")
    print(f"{'='*60}")

    assert result.get("type") == expected_type, f"Expected {expected_type}, got {result.get('type')}"
    assert (
        metrics.llm_call_count <= max_llm_calls
    ), f"Expected <= {max_llm_calls} LLM calls, got {metrics.llm_call_count}"


# ============================================================================
# Summary Report (run after all tests)
# ============================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print performance summary after tests complete."""
    terminalreporter.write_sep("=", "Performance Benchmark Summary")
    terminalreporter.write_line("See individual test output for LLM call counts and timing.")
