"""Cost + accuracy + latency eval for the suggester agent.

Fixtures live in ``evals/fixtures/suggester/*.yaml`` as one ``Case`` per
file. Each holds:

* ``docs_change`` — a mapping of doc paths to a stripped-down describer
  state entry (hash + ``DocSummary``-shaped summary), mirroring the shape
  the suggester service consumes in production
* ``code_change`` — the same shape for code files, with the
  ``CodeChanges``-shaped summary plus optional priority/metadata
* ``expected.suggestions`` — a list of ``{documentation_file_path,
  change_type, optional?}`` entries; ``optional: true`` marks
  suggestions that are acceptable but not required (they count toward
  precision but not recall)

Run with::

    uv run python -m evals.suggester_eval

Requires an OpenAI/Azure token in ``.env``. Uses the current tier of
:func:`get_suggester_agent` (gpt-5.6-terra at time of writing).

Scoring:

* ``file_path_recall`` — required expected files that the model produced
* ``file_path_precision`` — produced files that were in the accepted set
* ``file_path_f1`` — harmonic mean of the two
* ``change_type_accuracy`` — for produced files that were in the accepted
  set, fraction with the right ``ChangeType``
* ``cost_usd`` / ``tokens`` / ``requests`` per case via the same
  side-channel pattern as the other suites
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from dope.core.usage import UsageTracker
from dope.models.domain.documentation import DocSuggestions
from dope.models.enums import ChangeType
from dope.services.suggester import change_processor
from dope.services.suggester.prompts import SUGGESTION_PROMPT
from dope.services.suggester.suggester_agents import get_suggester_agent

FIXTURES = Path(__file__).parent / "fixtures" / "suggester"
MAX_CONCURRENCY = 3

_usage_by_case: dict[int, RunUsage] = {}


class SuggesterInput:
    """Bundle of doc + code state dicts fed to the suggester prompt."""

    def __init__(self, docs_change: dict[str, Any], code_change: dict[str, Any]) -> None:
        """Store the two state dicts."""
        self.docs_change = docs_change
        self.code_change = code_change


class ExpectedSuggestion:
    """One item in the fixture's ``expected.suggestions`` list."""

    def __init__(self, documentation_file_path: str, change_type: str, optional: bool = False):
        """Capture the target path and required change type; optional flag."""
        self.documentation_file_path = documentation_file_path
        self.change_type = ChangeType(change_type)
        self.optional = optional


class ExpectedSuggestions:
    """Container the pydantic-evals ``expected_output`` slot points at."""

    def __init__(self, suggestions: list[ExpectedSuggestion]):
        """Wrap the parsed suggestion list."""
        self.suggestions = suggestions


def _basename(path: str) -> str:
    """Return the leaf name for lenient path comparison across fixtures."""
    return Path(path).name.lower()


class SuggesterAccuracy(Evaluator[SuggesterInput, DocSuggestions]):
    """File-path F1 + change-type accuracy over the accepted expected set."""

    def evaluate(
        self, ctx: EvaluatorContext[SuggesterInput, DocSuggestions, dict]
    ) -> dict[str, float]:
        """Score the produced DocSuggestions against the fixture's expected list."""
        expected: ExpectedSuggestions | None = ctx.expected_output
        actual = ctx.output
        if expected is None:
            return {}

        required = {
            _basename(s.documentation_file_path) for s in expected.suggestions if not s.optional
        }
        accepted = {_basename(s.documentation_file_path) for s in expected.suggestions}
        expected_types = {
            _basename(s.documentation_file_path): s.change_type for s in expected.suggestions
        }

        produced = {_basename(s.documentation_file_path) for s in actual.changes_to_apply}
        produced_types = {
            _basename(s.documentation_file_path): s.change_type for s in actual.changes_to_apply
        }

        matched_required = required & produced
        matched_accepted = accepted & produced

        recall = len(matched_required) / len(required) if required else 1.0
        if produced:
            precision = len(matched_accepted) / len(produced)
        else:
            precision = 1.0 if not required else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        if matched_accepted:
            type_matches = sum(
                1 for name in matched_accepted if produced_types[name] == expected_types[name]
            )
            type_accuracy = type_matches / len(matched_accepted)
        else:
            type_accuracy = 1.0 if not required else 0.0

        return {
            "file_path_recall": recall,
            "file_path_precision": precision,
            "file_path_f1": f1,
            "change_type_accuracy": type_accuracy,
            "n_produced": float(len(produced)),
        }


class CostMetrics(Evaluator[SuggesterInput, DocSuggestions]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(
        self, ctx: EvaluatorContext[SuggesterInput, DocSuggestions, dict]
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


def _load_case(path: Path) -> Case[SuggesterInput, ExpectedSuggestions, dict]:
    data = yaml.safe_load(path.read_text())
    inputs = SuggesterInput(
        docs_change=data.get("docs_change", {}),
        code_change=data.get("code_change", {}),
    )
    expected_list = data.get("expected", {}).get("suggestions", []) or []
    expected = ExpectedSuggestions(
        suggestions=[ExpectedSuggestion(**s) for s in expected_list],
    )
    return Case(
        name=data["name"],
        inputs=inputs,
        expected_output=expected,
        metadata={"description": data.get("description", "").strip()},
    )


def build_dataset() -> Dataset[SuggesterInput, ExpectedSuggestions, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    return Dataset(
        name="suggester",
        cases=cases,
        evaluators=[SuggesterAccuracy(), CostMetrics()],
    )


def _build_prompt(inputs: SuggesterInput) -> str:
    """Mirror the production prompt shape from :class:`DocChangeSuggester`."""
    docs_formatted = change_processor.format_changes_for_prompt(
        inputs.docs_change, include_metadata=False
    )
    code_formatted = change_processor.format_changes_for_prompt(
        inputs.code_change, include_metadata=True
    )
    return SUGGESTION_PROMPT.format(documentation=docs_formatted, code_changes=code_formatted)


async def _run_suggester(inputs: SuggesterInput) -> DocSuggestions:
    """Task under evaluation; also stashes per-case usage for CostMetrics."""
    tracker = UsageTracker()
    prompt = _build_prompt(inputs)
    result = await get_suggester_agent().run(user_prompt=prompt, usage=tracker.usage)
    _usage_by_case[id(inputs)] = tracker.usage
    return result.output


def main() -> None:
    """Build the dataset, run the suggester agent on every fixture, print report."""
    dataset = build_dataset()
    report = dataset.evaluate_sync(_run_suggester, max_concurrency=MAX_CONCURRENCY)
    report.print(include_input=False, include_output=True, include_durations=True)


if __name__ == "__main__":
    main()
