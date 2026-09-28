"""Unit tests for dope.services.judge.judge_service."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from dope.core.classification import ChangeCategory
from dope.models.domain.judgment import DiffJudgment
from dope.models.enums import ChangeType
from dope.services.judge.judge_service import judge_diff

DEFAULT_OUTPUTS: dict[str, object] = {
    "get_change_category_agent": ChangeCategory.FEATURE,
    "get_change_type_agent": ChangeType.ADD,
    "get_is_breaking_agent": False,
    "get_is_user_facing_agent": True,
    "get_needs_docs_agent": True,
    "get_doc_priority_agent": 3,
}


def _make_agent(output_value, recorder=None, name=""):
    """Build a MagicMock Agent whose async run() yields output_value.

    If recorder is provided, run() also records its kwargs under `name`.
    """
    agent = MagicMock()

    async def _run(*_args, **kwargs):
        if recorder is not None:
            recorder[name] = kwargs
        result = MagicMock()
        result.output = output_value
        return result

    agent.run = _run
    return agent


@pytest.fixture
def patch_agents():
    """Factory that patches every get_*_agent with a canned-output MagicMock.

    Returns a helper: `install(recorder=None)` applies the patches and returns
    the mapping of factory name -> mocked Agent.
    """
    patchers: list = []

    def install(recorder=None):
        agents = {
            name: _make_agent(output, recorder=recorder, name=name)
            for name, output in DEFAULT_OUTPUTS.items()
        }
        for name, agent in agents.items():
            p = patch(f"dope.services.judge.judge_service.{name}", return_value=agent)
            p.start()
            patchers.append(p)
        return agents

    yield install
    for p in patchers:
        p.stop()


def test_judge_diff_assembles_all_fields(patch_agents):
    """judge_diff returns a DiffJudgment populated from the six agent outputs."""
    patch_agents()

    result = asyncio.run(judge_diff("diff --git a/foo b/foo\n+def bar(): ..."))

    assert isinstance(result, DiffJudgment)
    assert result.change_category == ChangeCategory.FEATURE
    assert result.change_type == ChangeType.ADD
    assert result.is_breaking is False
    assert result.is_user_facing is True
    assert result.needs_docs is True
    assert result.doc_priority == 3


def test_judge_diff_forwards_usage_from_tracker(patch_agents):
    """When a usage_tracker is provided, its .usage is forwarded to every agent."""
    calls: dict[str, dict] = {}
    patch_agents(recorder=calls)
    tracker = MagicMock()
    sentinel = MagicMock(name="usage-sentinel")
    tracker.usage = sentinel

    asyncio.run(judge_diff("some diff", usage_tracker=tracker))

    assert len(calls) == 6
    for kwargs in calls.values():
        assert kwargs["usage"] is sentinel
        assert kwargs["user_prompt"] == "some diff"


def test_judge_diff_without_tracker_passes_none_usage(patch_agents):
    """Without a tracker, agents are called with usage=None."""
    calls: dict[str, dict] = {}
    patch_agents(recorder=calls)

    asyncio.run(judge_diff("diff"))

    assert len(calls) == 6
    for kwargs in calls.values():
        assert kwargs["usage"] is None
