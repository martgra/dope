"""Prompt A/B compare production CHANGE_DOC_PROMPT vs the tightened variant.

Same shape as :mod:`evals.changer_ab` but the axis being swapped is the
system prompt, not the model. Model is held constant at the production
tier (default ``gpt-5.6-sol``).

Run with::

    uv run python -m evals.changer_prompt_ab
    uv run python -m evals.changer_prompt_ab --model gpt-5.6-terra

Reports the delta on both quality and cost. The tightened prompt is
expected to raise ``content_similarity`` (less over-rewriting) and lower
``char_delta_ratio`` (less bloat) without hurting the LLM-judge assertion
pass rate.
"""

from __future__ import annotations

import argparse

from evals.changer_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_changer,
)
from evals.prompt_variants import CHANGE_DOC_PROMPT_MINIMAL


def run_ab(model: str) -> None:
    """Run production prompt then tightened variant on the same dataset."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: production CHANGE_DOC_PROMPT ({model}) ===\n")
    _usage_by_case.clear()
    baseline = dataset.evaluate_sync(
        make_run_changer(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    baseline.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: CHANGE_DOC_PROMPT_MINIMAL ({model}) ===\n")
    _usage_by_case.clear()
    challenger = dataset.evaluate_sync(
        make_run_changer(model_name=model, system_prompt=CHANGE_DOC_PROMPT_MINIMAL),
        max_concurrency=MAX_CONCURRENCY,
    )
    challenger.print(
        baseline=baseline,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse --model, run the prompt A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="gpt-5.6-sol", help="model held constant across both runs"
    )
    args = parser.parse_args()
    run_ab(args.model)


if __name__ == "__main__":
    main()
