"""A/B compare the production aligner vs. aligner + post-hoc Jev minimality gate.

Baseline: :mod:`evals.doc_aligner_eval` — production aligner, full-content
output, ``scope.align_doc`` at the manifest-pinned version (``v2-minimal``).

Challenger: same aligner call, then a Jev Noul
(:func:`dope.services.judge.judge_service.judge_alignment_preserves_scope`)
inspects (scope, original, aligned). If Jev says the rewrite over-touched
lines the scope didn't require, the challenger falls back to the original
file content — turning an over-rewrite into a no-op. If Jev approves,
the aligner output is used verbatim.

Both runs are scored on the same evaluators (ContentSimilarity,
PreservedSpecifics, four LLMJudge rubrics, cross-file changes count,
cost/tokens/requests). The gate spends one extra Jev call per fixture;
the win, if any, shows up as higher ``content_similarity``, lower
``char_delta_ratio``, and higher ``minimal_change`` pass rate — at the
cost of some ``incorporates_scope`` pass rate when the gate over-rejects.

Run with::

    uv run python -m evals.doc_aligner_minimality_gate_ab
    uv run python -m evals.doc_aligner_minimality_gate_ab --model gpt-5.6-luna
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse

from dope.core.usage import UsageTracker
from dope.models.domain.scope import AlignedScope
from dope.services.judge.judge_service import judge_alignment_preserves_scope
from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    DocAlignerInput,
    _build_user_prompt,
    _usage_by_case,
    build_dataset,
    build_doc_aligner_agent,
    make_run_doc_aligner,
)


def make_run_gated_aligner(model_name: str | None = None):
    """Task factory: run aligner, then gate the output through Jev.

    The tracker in play is the same one the baseline uses, so the Jev
    call's token spend is included in ``cost_usd`` / ``requests`` /
    ``tokens`` reported by :class:`CostMetrics` — the eval measures the
    gate's TRUE cost, not just the aligner's.
    """
    agent = build_doc_aligner_agent(model_name)

    async def _run(inputs: DocAlignerInput) -> AlignedScope:
        tracker = UsageTracker()
        prompt = _build_user_prompt(inputs)
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        aligned = result.output
        preserved = await judge_alignment_preserves_scope(
            scope=inputs.scope_summary,
            original_content=inputs.file_content,
            aligned_content=aligned.content,
            moves=aligned.changes_in_other_files,
            usage_tracker=tracker,
        )
        _usage_by_case[id(inputs)] = tracker.usage
        if preserved:
            return aligned
        return AlignedScope(
            content=inputs.file_content,
            changes_in_other_files=aligned.changes_in_other_files,
        )

    return _run


def run_ab(model: str) -> None:
    """Baseline (no gate) then challenger (gate) on the same fixtures."""
    dataset = build_dataset()

    print(f"\n=== BASELINE: production aligner, no gate ({model}) ===\n")
    _usage_by_case.clear()
    baseline_report = dataset.evaluate_sync(
        make_run_doc_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    baseline_report.print(include_input=False, include_output=False, include_durations=True)

    print(f"\n=== CHALLENGER: aligner + Jev minimality gate ({model}) ===\n")
    _usage_by_case.clear()
    challenger_report = dataset.evaluate_sync(
        make_run_gated_aligner(model_name=model), max_concurrency=MAX_CONCURRENCY
    )
    challenger_report.print(
        baseline=baseline_report,
        include_input=False,
        include_output=False,
        include_durations=True,
    )


def main() -> None:
    """CLI entrypoint: parse --model, run the gate A/B."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="gpt-5.6-terra", help="aligner model held constant across both runs"
    )
    args = parser.parse_args()
    run_ab(args.model)


if __name__ == "__main__":
    main()
