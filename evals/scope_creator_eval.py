"""Cost + accuracy + latency eval for the scope_creator agent.

Fixtures live in ``evals/fixtures/scope_creator/*.yaml``. Each holds:

* ``scope_documents`` — list of ``DocTemplateKey`` strings that the scope
  requires. A minimal scope with these keys is synthesized on the fly
  (the full scope template shape carries hundreds of lines of section
  metadata that this eval does not need to exercise)
* ``doc_structure`` — string tree of existing doc files in the repo
* ``code_structure`` — string tree of code files in the repo
* ``expected`` — mapping of ``doc_key -> filepath`` (or ``[list, of,
  accepted, paths]`` when several plausible paths exist)

Run with::

    uv run python -m evals.scope_creator_eval

Requires an OpenAI/Azure token in ``.env``. Uses whatever tier
:func:`get_scope_creator_agent` is currently pinned to (``gpt-5.6-terra``
at time of writing).

Scoring:

* ``key_coverage`` — fraction of expected keys that appear in the output
* ``path_accuracy`` — fraction of produced entries whose value matches
  any of the accepted paths for that key
* ``no_extra_keys`` — 1.0 if the output does not invent extra keys,
  else the fraction of produced keys that were expected
* ``cost_usd`` / ``tokens`` / ``requests`` per case
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from dope.core.usage import UsageTracker
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry
from dope.services.scoper.scoper_agents import get_scope_creator_agent

FIXTURES = Path(__file__).parent / "fixtures" / "scope_creator"
MAX_CONCURRENCY = 3

_usage_by_case: dict[int, RunUsage] = {}


class ScopeCreatorInput(BaseModel):
    """Inputs the scope_creator agent needs to map doc keys to paths."""

    scope_documents: list[str]
    doc_structure: str
    code_structure: str


class ExpectedPaths(BaseModel):
    """Per-key expected paths, either a single string or a list of accepted alternatives."""

    mapping: dict[str, str | list[str]]


def _accepts_path(actual: str, expected: str | list[str]) -> bool:
    """Return True when ``actual`` matches ``expected`` (or one of the alternatives)."""
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


class ScopeMappingAccuracy(Evaluator[ScopeCreatorInput, dict[str, str]]):
    """Score key coverage + path accuracy + no-extra-keys."""

    def evaluate(
        self, ctx: EvaluatorContext[ScopeCreatorInput, dict[str, str], dict]
    ) -> dict[str, float]:
        """Return one score per axis; missing expected is a coverage miss."""
        expected: ExpectedPaths | None = ctx.expected_output
        actual = ctx.output or {}
        if expected is None:
            return {}
        exp = expected.mapping
        expected_keys = set(exp.keys())
        produced_keys = set(actual.keys())
        matched_keys = expected_keys & produced_keys
        coverage = len(matched_keys) / len(expected_keys) if expected_keys else 1.0
        path_hits = sum(1 for k in matched_keys if _accepts_path(actual[k], exp[k]))
        path_accuracy = path_hits / len(matched_keys) if matched_keys else 0.0
        extras = produced_keys - expected_keys
        no_extra = 1.0 - (len(extras) / len(produced_keys) if produced_keys else 0.0)
        return {
            "key_coverage": coverage,
            "path_accuracy": path_accuracy,
            "no_extra_keys": no_extra,
            "n_produced": float(len(produced_keys)),
        }


class CostMetrics(Evaluator[ScopeCreatorInput, dict[str, str]]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(
        self, ctx: EvaluatorContext[ScopeCreatorInput, dict[str, str], dict]
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


def _load_case(path: Path) -> Case[ScopeCreatorInput, ExpectedPaths, dict]:
    data = yaml.safe_load(path.read_text())
    inputs = ScopeCreatorInput(
        scope_documents=data["scope_documents"],
        doc_structure=data["doc_structure"],
        code_structure=data["code_structure"],
    )
    expected = ExpectedPaths(mapping=data["expected"])
    return Case(
        name=data["name"],
        inputs=inputs,
        expected_output=expected,
        metadata={"description": data.get("description", "").strip()},
    )


def build_dataset() -> Dataset[ScopeCreatorInput, ExpectedPaths, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    return Dataset(
        name="scope_creator",
        cases=cases,
        evaluators=[ScopeMappingAccuracy(), CostMetrics()],
    )


def build_scope_creator_agent(model_name: str | None = None) -> Agent[None, dict[str, str]]:
    """Construct a scope_creator agent for the given model name.

    ``None`` returns the production factory's agent (``gpt-5.6-terra``);
    any other model name builds a fresh Agent with the same output_type
    and system prompt but a different underlying model, for use by an
    A/B runner.
    """
    if model_name is None:
        return get_scope_creator_agent()
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(
        model=get_model(settings.agent.provider, model_name),
        output_type=dict[str, str],
    )

    @agent.system_prompt
    def _add_prompt() -> str:
        return PromptRegistry.get("scope.creator").template

    return agent


def _build_user_prompt(inputs: ScopeCreatorInput) -> str:
    """Mirror the shape of :meth:`ScopeService.suggest_structure`'s prompt."""
    return f"""
Here is the doc overview:
{inputs.doc_structure}

Here is the code overview:
{inputs.code_structure}

Here are the document keys to be filled into the dict {inputs.scope_documents}:

Based on this information, suggest a structure for the documentation where you map
existing paths in the implemented doc structure to documents to relevant documents in
the structure.
"""


def make_run_scope_creator(model_name: str | None = None):
    """Factory that binds a model to the task wrapper used by evaluate_sync."""
    agent = build_scope_creator_agent(model_name)

    async def _run(inputs: ScopeCreatorInput) -> dict[str, str]:
        tracker = UsageTracker()
        prompt = _build_user_prompt(inputs)
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        _usage_by_case[id(inputs)] = tracker.usage
        return result.output

    return _run


def main() -> None:
    """Build the dataset, run the scope_creator on every fixture, print report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="override model")
    args = parser.parse_args()
    dataset = build_dataset()
    report = dataset.evaluate_sync(
        make_run_scope_creator(args.model), max_concurrency=MAX_CONCURRENCY
    )
    report.print(include_input=False, include_output=True, include_durations=True)


if __name__ == "__main__":
    main()
