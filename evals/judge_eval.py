"""Cost + accuracy + latency eval for :func:`dope.services.judge.judge_diff`.

Fixtures live in ``evals/fixtures/judge/*.yaml`` as one ``Case`` per file:
a ``diff`` string plus an ``expected`` mapping of the six ``DiffJudgment``
fields. Categorical fields (``change_category``, ``change_type``) may be
either a single string OR a list of accepted alternatives for genuinely
ambiguous cases (e.g. ``[api, refactor]`` for a public rename).

Run with::

    uv run python -m evals.judge_eval

Requires ``typesafe__API_KEY`` in ``.env``. Each case fires six Jev agents
in parallel via :func:`judge_diff`; pydantic-evals runs cases concurrently
subject to :data:`MAX_CONCURRENCY`.

Cost/token/request counts are captured per case via a fresh
:class:`UsageTracker` inside the task wrapper and stashed in a
module-level dict keyed by diff string; the :class:`CostMetrics`
evaluator reads them back so the report renders cost alongside accuracy.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from dope.core.classification import ChangeCategory
from dope.core.usage import UsageTracker
from dope.models.domain.judgment import DiffJudgment
from dope.models.enums import ChangeType
from dope.services.judge import judge_diff

FIXTURES = Path(__file__).parent / "fixtures" / "judge"
MAX_CONCURRENCY = 5

# Side channel: per-diff usage captured by the task wrapper, read by the
# CostMetrics evaluator. Fresh dict per Python process; each diff string
# is a unique key so concurrent writes don't collide.
_usage_by_diff: dict[str, RunUsage] = {}


def _accepts(actual: Any, expected: Any) -> float:
    """Score 1.0 when actual matches expected (or any of a list of accepted)."""
    if isinstance(expected, list):
        return float(actual in expected or (hasattr(actual, "value") and actual.value in expected))
    return float(actual == expected or (hasattr(actual, "value") and actual.value == expected))


class DiffJudgmentFields(Evaluator[str, DiffJudgment]):
    """Per-field exact-match score against the gold expected values."""

    def evaluate(self, ctx: EvaluatorContext[str, DiffJudgment, dict]) -> dict[str, float]:
        """Return one score per DiffJudgment field."""
        expected = ctx.expected_output
        actual = ctx.output
        if expected is None:
            return {}
        exp_meta = ctx.metadata or {}
        raw_expected = exp_meta.get("raw_expected", {})
        return {
            "change_category": _accepts(actual.change_category, raw_expected["change_category"]),
            "change_type": _accepts(actual.change_type, raw_expected["change_type"]),
            "is_breaking": float(actual.is_breaking == expected.is_breaking),
            "is_user_facing": float(actual.is_user_facing == expected.is_user_facing),
            "needs_docs": float(actual.needs_docs == expected.needs_docs),
            "doc_priority_exact": float(actual.doc_priority == expected.doc_priority),
            "doc_priority_within_1": float(abs(actual.doc_priority - expected.doc_priority) <= 1),
        }


class CostMetrics(Evaluator[str, DiffJudgment]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(self, ctx: EvaluatorContext[str, DiffJudgment, dict]) -> dict[str, float]:
        """Return cost/tokens/requests captured by the task wrapper."""
        usage = _usage_by_diff.get(ctx.inputs)
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


def _load_case(path: Path) -> Case[str, DiffJudgment, dict]:
    data = yaml.safe_load(path.read_text())
    e = data["expected"]
    # expected_output uses the FIRST alternative for each categorical field
    # so pydantic-evals has one concrete value to display; the evaluator uses
    # metadata["raw_expected"] to score against the full accepted set.
    expected = DiffJudgment(
        change_category=ChangeCategory(_first(e["change_category"])),
        change_type=ChangeType(_first(e["change_type"])),
        is_breaking=e["is_breaking"],
        is_user_facing=e["is_user_facing"],
        needs_docs=e["needs_docs"],
        doc_priority=e["doc_priority"],
    )
    return Case(
        name=data["name"],
        inputs=data["diff"],
        expected_output=expected,
        metadata={
            "description": data.get("description", "").strip(),
            "raw_expected": e,
        },
    )


def build_dataset() -> Dataset[str, DiffJudgment, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    return Dataset(
        name="judge_diff",
        cases=cases,
        evaluators=[DiffJudgmentFields(), CostMetrics()],
    )


async def _run_judge(diff: str) -> DiffJudgment:
    """Task under evaluation; also stashes per-case usage for CostMetrics."""
    tracker = UsageTracker()
    result = await judge_diff(diff, usage_tracker=tracker)
    _usage_by_diff[diff] = tracker.usage
    return result


def main() -> None:
    """Build the dataset, run judge_diff against every fixture, print report."""
    dataset = build_dataset()
    report = dataset.evaluate_sync(_run_judge, max_concurrency=MAX_CONCURRENCY)
    report.print(include_input=False, include_output=True, include_durations=True)


if __name__ == "__main__":
    main()
