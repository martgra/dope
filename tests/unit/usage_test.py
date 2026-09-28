"""Tests for LLM usage tracking."""

from pydantic_ai.usage import RunUsage

from dope.core.usage import UsageTracker


def test_usage_tracker_initializes_pydantic_ai_run_usage() -> None:
    """Initialize a tracker with Pydantic AI's current usage type."""
    tracker = UsageTracker()

    assert isinstance(tracker.usage, RunUsage)
    assert tracker.usage.total_tokens == 0
