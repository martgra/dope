"""Cost + accuracy + latency eval for the project-complexity scoper agent.

Fixtures live in ``evals/fixtures/project_complexity/*.yaml`` as one ``Case``
per file: a ``metadata`` mapping (matching :class:`CodeMetadata`) + a
``structure`` string + an ``expected`` :class:`ProjectTier` value. The
``expected`` may be a list of two adjacent tiers when the case is
genuinely borderline (e.g. ``[small, medium]``).

Run with::

    uv run python -m evals.project_complexity_eval

Requires an OpenAI/Azure token in ``.env``. Uses whatever tier
:func:`get_project_complexity_agent` is currently pinned to (gpt-5.6-luna
at time of writing).

Cost/token/request counts are captured per case via a fresh
:class:`UsageTracker` and stashed in a module-level dict keyed by the
input's ``id()``; the :class:`CostMetrics` evaluator reads them back.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from dope.core.usage import UsageTracker
from dope.models.domain.code import CodeMetadata
from dope.models.enums import ProjectTier
from dope.prompts import PromptRegistry
from dope.services.scoper.scoper_agents import get_project_complexity_agent

FIXTURES = Path(__file__).parent / "fixtures" / "project_complexity"
MAX_CONCURRENCY = 5

_TIER_ORDER = [
    ProjectTier.trivial,
    ProjectTier.small,
    ProjectTier.medium,
    ProjectTier.large,
    ProjectTier.massive,
]
_TIER_INDEX = {t: i for i, t in enumerate(_TIER_ORDER)}


class ComplexityInput(BaseModel):
    """Input state fed to the project-complexity agent."""

    structure: str
    metadata: CodeMetadata


_usage_by_case: dict[int, RunUsage] = {}


def _accepts_tier(actual: ProjectTier, expected: Any) -> float:
    """Score 1.0 when actual is expected (or any of a list of accepted)."""
    if isinstance(expected, list):
        return float(actual.value in expected or actual in expected)
    return float(actual.value == expected or actual == expected)


class ProjectTierScore(Evaluator[ComplexityInput, ProjectTier]):
    """Score exact-match + within-1-tier distance + absolute error."""

    def evaluate(
        self, ctx: EvaluatorContext[ComplexityInput, ProjectTier, dict]
    ) -> dict[str, float]:
        """Return exact-match, within-1-tier, and absolute-tier-distance scores."""
        expected = ctx.expected_output
        actual = ctx.output
        if expected is None:
            return {}
        raw_expected = (ctx.metadata or {}).get("raw_expected", expected.value)
        exact = _accepts_tier(actual, raw_expected)
        if isinstance(raw_expected, list):
            expected_indices = [_TIER_INDEX[ProjectTier(v)] for v in raw_expected]
            distance = min(abs(_TIER_INDEX[actual] - i) for i in expected_indices)
        else:
            expected_idx = _TIER_INDEX[ProjectTier(raw_expected)]
            distance = abs(_TIER_INDEX[actual] - expected_idx)
        return {
            "tier_exact": exact,
            "tier_within_1": float(distance <= 1),
            "tier_distance": float(distance),
        }


class CostMetrics(Evaluator[ComplexityInput, ProjectTier]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(
        self, ctx: EvaluatorContext[ComplexityInput, ProjectTier, dict]
    ) -> dict[str, float]:
        """Return cost/tokens/requests captured by the task wrapper."""
        usage = _usage_by_case.get(id(ctx.inputs))
        if usage is None:
            return {}
        return {
            "cost_usd": float(usage.cost or 0),
            "tokens": float(usage.total_tokens or 0),
            "requests": float(usage.requests or 0),
        }


def _first(v: Any) -> Any:
    """Return the first alternative when ``v`` is a list, else ``v`` itself."""
    return v[0] if isinstance(v, list) else v


def _load_case(path: Path) -> Case[ComplexityInput, ProjectTier, dict]:
    data = yaml.safe_load(path.read_text())
    inputs = ComplexityInput(
        structure=data["structure"],
        metadata=CodeMetadata(**data["metadata"]),
    )
    expected = ProjectTier(_first(data["expected"]))
    return Case(
        name=data["name"],
        inputs=inputs,
        expected_output=expected,
        metadata={
            "description": data.get("description", "").strip(),
            "raw_expected": data["expected"],
        },
    )


def build_dataset() -> Dataset[ComplexityInput, ProjectTier, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    return Dataset(
        name="project_complexity",
        cases=cases,
        evaluators=[ProjectTierScore(), CostMetrics()],
    )


async def _run_complexity(inputs: ComplexityInput) -> ProjectTier:
    """Task under evaluation; also stashes per-case usage for CostMetrics."""
    tracker = UsageTracker()
    result = await get_project_complexity_agent().run(
        user_prompt=PromptRegistry.get("scope.complexity_user_template").render(
            structure=inputs.structure, metadata=inputs.metadata
        ),
        usage=tracker.usage,
    )
    _usage_by_case[id(inputs)] = tracker.usage
    return result.output


def main() -> None:
    """Build the dataset, run the complexity agent on every fixture, print report."""
    dataset = build_dataset()
    report = dataset.evaluate_sync(_run_complexity, max_concurrency=MAX_CONCURRENCY)
    report.print(include_input=False, include_output=True, include_durations=True)


if __name__ == "__main__":
    main()
