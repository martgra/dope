"""Prompt A/B compare two versions of ``scope.align_doc`` from the registry.

Model is held constant at the production tier (default ``gpt-5.6-sol``).

Run with::

    uv run python -m evals.doc_aligner_prompt_ab
    uv run python -m evals.doc_aligner_prompt_ab --baseline v1 --challenger v2-minimal
    uv run python -m evals.doc_aligner_prompt_ab --model gpt-5.6-terra
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from dope.prompts import PromptRegistry
from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_doc_aligner,
)


def run_ab(model: str, baseline_version: str, challenger_version: str) -> None:
    """Run baseline prompt then challenger on the same dataset."""
    dataset = build_dataset()
    baseline_prompt = PromptRegistry.get("scope.align_doc", version=baseline_version)
    challenger_prompt = PromptRegistry.get("scope.align_doc", version=challenger_version)

    print(f"\n=== BASELINE: scope.align_doc {baseline_prompt.version} ({model}) ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_doc_aligner(model_name=model, system_prompt=baseline_prompt.template),
        max_concurrency=MAX_CONCURRENCY,
    )
    baseline_report.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: scope.align_doc {challenger_prompt.version} ({model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_doc_aligner(model_name=model, system_prompt=challenger_prompt.template),
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
        "--model", default="gpt-5.6-sol", help="model held constant across both runs"
    )
    parser.add_argument("--baseline", default="v1", help="baseline prompt version")
    parser.add_argument("--challenger", default="v2-minimal", help="challenger prompt version")
    args = parser.parse_args()
    run_ab(args.model, args.baseline, args.challenger)


if __name__ == "__main__":
    main()
