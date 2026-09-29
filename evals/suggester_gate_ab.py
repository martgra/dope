"""A/B compare the suggester with vs without the Jev judgment gate.

The gate is the second half of the Jev wiring landed in commit 638826a.
When ``ScopeFilterSettings.enable_judgment_gate`` is true,
:func:`dope.services.suggester.change_processor.filter_by_judgment_needs_docs`
drops code changes whose ``DiffJudgment.needs_docs`` is explicitly false
BEFORE the suggester agent runs. Files without a judgment are always
kept.

The production ``DocChangeSuggester.get_suggestions`` reads the setting
and applies the gate; this A/B replicates that path in the eval's task
wrapper so we can measure the gate's effect on the same fixture set
that the prompt A/B runs against, without dragging in scope filtering
or doc-term filtering.

Run with::

    uv run python -m evals.suggester_gate_ab
    uv run python -m evals.suggester_gate_ab --model gpt-5.6-terra
"""

from __future__ import annotations

import argparse

from dope.core.usage import UsageTracker
from dope.models.domain.documentation import DocSuggestions
from dope.services.suggester import change_processor
from evals.suggester_eval import (
    MAX_CONCURRENCY,
    SuggesterInput,
    _build_prompt,
    _usage_by_case,
    build_dataset,
    build_suggester_agent,
    make_run_suggester,
)


def make_run_gated(model_name: str | None = None):
    """Task wrapper that applies filter_by_judgment_needs_docs before the LLM.

    When every code change gets dropped, returns an empty DocSuggestions
    without calling the agent at all — matching production behavior of
    :meth:`DocChangeSuggester.get_suggestions` and saving the call cost.
    """
    agent = build_suggester_agent(model_name)

    async def _run(inputs: SuggesterInput) -> DocSuggestions:
        gated_code = change_processor.filter_by_judgment_needs_docs(inputs.code_change)
        tracker = UsageTracker()
        _usage_by_case[id(inputs)] = tracker.usage
        if not gated_code:
            return DocSuggestions(changes_to_apply=[])
        gated_inputs = SuggesterInput(
            docs_change=inputs.docs_change,
            code_change=gated_code,
        )
        prompt = _build_prompt(gated_inputs)
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        return result.output

    return _run


def run_ab(model: str) -> None:
    """Baseline (no gate) vs challenger (gate on) on the same dataset."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: gate off ({model}) ===\n")
    _usage_by_case.clear()
    baseline = dataset.evaluate_sync(
        make_run_suggester(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    baseline.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: gate on ({model}) ===\n")
    _usage_by_case.clear()
    challenger = dataset.evaluate_sync(
        make_run_gated(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    challenger.print(
        baseline=baseline,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse --model, run the gate A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="gpt-5.6-luna", help="model held constant across both runs"
    )
    args = parser.parse_args()
    run_ab(args.model)


if __name__ == "__main__":
    main()
