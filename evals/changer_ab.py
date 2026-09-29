"""A/B compare two model tiers on the changer eval fixtures.

Runs :mod:`evals.changer_eval`'s dataset twice — once against a baseline
model (default ``gpt-5.6-sol``, matching production) and once against a
challenger (default ``gpt-5.6-terra``) — then prints both reports and the
delta via pydantic-evals' ``baseline=`` renderer.

Scoring uses four LLM-as-judge rubrics (incorporates suggestion, preserves
structure, no hallucinations, valid markdown) evaluated by
``gpt-5.6-terra`` (a neutral middle-tier judge). Terra is used for judging
even when it is one of the compared models — this is a known bias but is
tolerable in the absence of a true third-party judge model.

Run with::

    uv run python -m evals.changer_ab
    uv run python -m evals.changer_ab --baseline gpt-5.6-sol --challenger gpt-5.6-luna

Cost at 4 fixtures x 2 rewrites x ~2k output tokens each: roughly ``$0.20``
for sol, ``$0.04`` for terra, ``$0.005`` for luna, plus ``~$0.10`` in
judge calls.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from evals.changer_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_changer,
)


def run_ab(baseline_model: str, challenger_model: str) -> None:
    """Run both models on the same dataset and print the delta report."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: {baseline_model} ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_changer(baseline_model), max_concurrency=MAX_CONCURRENCY
    )
    baseline_report.print(
        include_input=False,
        include_output=False,
        include_durations=True,
    )

    print(f"\n=== CHALLENGER: {challenger_model} (vs {baseline_model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_changer(challenger_model), max_concurrency=MAX_CONCURRENCY
    )
    challenger_report.print(
        baseline=baseline_report,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse --baseline/--challenger, run the A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="gpt-5.6-sol", help="baseline model")
    parser.add_argument("--challenger", default="gpt-5.6-terra", help="challenger model")
    args = parser.parse_args()
    run_ab(args.baseline, args.challenger)


if __name__ == "__main__":
    main()
