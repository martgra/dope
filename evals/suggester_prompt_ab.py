"""Prompt A/B compare two versions of ``suggest.system`` from the registry.

Same shape as :mod:`evals.changer_prompt_ab` but for the suggester
service. Model is held constant at the production tier
(default ``gpt-5.6-luna``, matching the flip in commit 5243810).

The v2-judgment challenger is only useful on fixtures whose code_change
entries carry a ``summary.judgment`` block — the six fields
:mod:`dope.services.suggester.change_processor` now surfaces as
first-class metadata. Fixtures without judgment behave like v1 under
both prompts.

Run with::

    uv run python -m evals.suggester_prompt_ab
    uv run python -m evals.suggester_prompt_ab --baseline v1 --challenger v2-judgment
    uv run python -m evals.suggester_prompt_ab --model gpt-5.6-terra
"""

from __future__ import annotations

import argparse

from dope.prompts import PromptRegistry
from evals.suggester_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_suggester,
)


def run_ab(model: str, baseline_version: str, challenger_version: str) -> None:
    """Run baseline prompt then challenger on the same dataset."""
    dataset = build_dataset()
    baseline_prompt = PromptRegistry.get("suggest.system", version=baseline_version)
    challenger_prompt = PromptRegistry.get("suggest.system", version=challenger_version)

    print(f"\n=== BASELINE: suggest.system {baseline_prompt.version} ({model}) ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_suggester(model_name=model, system_prompt=baseline_prompt.template),
        max_concurrency=MAX_CONCURRENCY,
    )
    baseline_report.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: suggest.system {challenger_prompt.version} ({model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_suggester(model_name=model, system_prompt=challenger_prompt.template),
        max_concurrency=MAX_CONCURRENCY,
    )
    challenger_report.print(
        baseline=baseline_report,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse args, run the prompt A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="gpt-5.6-luna", help="model held constant across both runs"
    )
    parser.add_argument("--baseline", default="v1", help="baseline prompt version")
    parser.add_argument("--challenger", default="v2-judgment", help="challenger prompt version")
    args = parser.parse_args()
    run_ab(args.model, args.baseline, args.challenger)


if __name__ == "__main__":
    main()
