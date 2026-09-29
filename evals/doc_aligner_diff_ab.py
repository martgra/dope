"""A/B compare the production (full-content) aligner against the diff-based variant.

Baseline: :mod:`evals.doc_aligner_eval` — production aligner, full-content
output, ``scope.align_doc`` at whatever the manifest pins (currently
``v2-minimal``).

Challenger: :mod:`evals.doc_aligner_diff_eval` — diff-based aligner
bound to ``scope.align_doc`` version ``v3-diff``; outputs
:class:`EditedScope` and reconstructs content via
:func:`apply_edits`. The reconstructed content is graded on the exact
same evaluators as the baseline (including ``content_similarity``,
``preserved_specifics``, and the four LLMJudge rubrics), so a
head-to-head comparison is apples-to-apples.

Run with::

    uv run python -m evals.doc_aligner_diff_ab
    uv run python -m evals.doc_aligner_diff_ab --model gpt-5.6-terra
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from evals.doc_aligner_diff_eval import make_run_diff_aligner
from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_doc_aligner,
)


def run_ab(model: str) -> None:
    """Run production full-content aligner then diff-based aligner on same fixtures."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: full-content aligner ({model}) ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_doc_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    baseline_report.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: diff-based aligner v3-diff ({model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_diff_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    challenger_report.print(
        baseline=baseline_report,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse --model, run the architecture A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="gpt-5.6-sol", help="model held constant across both runs"
    )
    args = parser.parse_args()
    run_ab(args.model)


if __name__ == "__main__":
    main()
