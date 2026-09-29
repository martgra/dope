"""A/B compare the production full-content aligner vs narrow-diff v4-diff-narrow.

Baseline: :mod:`evals.doc_aligner_eval` — production aligner, full-content
output, ``scope.align_doc`` at the manifest-pinned version
(``v2-minimal``).

Challenger: :mod:`evals.doc_aligner_narrow_diff_eval` — narrow-diff
aligner (``NarrowEditedScope`` output, ``v4-diff-narrow`` prompt).
The narrow schema forbids ``replace_range`` — the v3-diff failure mode
was replace_range abuse.

Both runs are scored on the same evaluators (ContentSimilarity,
PreservedSpecifics, four LLMJudge rubrics, cross-file changes).

Run with::

    uv run python -m evals.doc_aligner_narrow_diff_ab
    uv run python -m evals.doc_aligner_narrow_diff_ab --model gpt-5.6-luna
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    _usage_by_case,
    build_dataset,
    make_run_doc_aligner,
)
from evals.doc_aligner_narrow_diff_eval import make_run_narrow_diff_aligner


def run_ab(model: str) -> None:
    """Baseline (full-content) then challenger (narrow-diff) on same fixtures."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: full-content aligner ({model}) ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_doc_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    baseline_report.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: narrow-diff v4-diff-narrow ({model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_narrow_diff_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
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
        "--model", default="gpt-5.6-terra", help="model held constant across both runs"
    )
    args = parser.parse_args()
    run_ab(args.model)


if __name__ == "__main__":
    main()
