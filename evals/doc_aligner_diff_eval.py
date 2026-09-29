"""Eval for the diff-based doc_aligner variant.

Reuses every fixture, every LLMJudge rubric, and every char-level
evaluator from :mod:`evals.doc_aligner_eval`. The only differences are:

* A separate agent with ``output_type=EditedScope`` bound to the
  ``scope.align_doc`` version ``v3-diff`` prompt from the registry
* A task wrapper that:
  - Prefixes source lines with 1-based numbers so the model can
    address edits by line
  - Runs the agent, then reconstructs the final content via
    :func:`apply_edits`
  - Returns an :class:`AlignedScope` with that reconstructed content
    so the shared evaluators plug in unchanged

Run with::

    uv run python -m evals.doc_aligner_diff_eval

The comparison against the production ``v2-minimal`` full-content
aligner lives in :mod:`evals.doc_aligner_diff_ab`.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse
from typing import cast

from pydantic_ai import Agent

from dope.core.usage import UsageTracker
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.domain.scope import AlignedScope, EditedScope, apply_edits
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry
from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    DocAlignerInput,
    _usage_by_case,
    build_dataset,
)


def _number_lines(text: str) -> str:
    """Prefix each line with ``N| `` where N is 1-based."""
    lines = text.splitlines()
    width = len(str(max(len(lines), 1)))
    return "\n".join(f"{i:>{width}}| {line}" for i, line in enumerate(lines, start=1))


def build_diff_aligner_agent(model_name: str | None = None) -> Agent[None, EditedScope]:
    """Construct a diff-output aligner agent bound to the v3-diff prompt."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    resolved_model = model_name or "gpt-5.6-sol"
    prompt = PromptRegistry.get("scope.align_doc", version="v3-diff")
    agent = Agent(
        model=get_model(settings.agent.provider, resolved_model),
        output_type=EditedScope,
    )

    @agent.system_prompt
    def _add_prompt() -> str:
        return prompt.template

    return agent


def make_run_diff_aligner(model_name: str | None = None):
    """Task factory: run the diff aligner and reconstruct AlignedScope.

    The reconstructed content plugs into the shared evaluators (which
    expect ``output.content: str``) so the diff variant is scored on
    the same axes as the production full-content aligner.
    """
    agent = build_diff_aligner_agent(model_name)
    user_prompt = PromptRegistry.get("scope.align_doc_diff_user_template", version="v1")

    async def _run(inputs: DocAlignerInput) -> AlignedScope:
        tracker = UsageTracker()
        prompt = user_prompt.render(
            scope=inputs.scope_summary,
            filepath=inputs.filepath,
            numbered_content=_number_lines(inputs.file_content),
        )
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        edited: EditedScope = cast(EditedScope, result.output)
        reconstructed = apply_edits(inputs.file_content, edited.edits)
        _usage_by_case[id(inputs)] = tracker.usage
        return AlignedScope(
            content=reconstructed,
            changes_in_other_files=edited.changes_in_other_files,
        )

    return _run


def main() -> None:
    """Build the dataset, run the diff-based aligner, print report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="override model (default: gpt-5.6-sol)")
    args = parser.parse_args()
    dataset = build_dataset()
    report = dataset.evaluate_sync(
        make_run_diff_aligner(args.model), max_concurrency=MAX_CONCURRENCY
    )
    report.print(include_input=False, include_output=False, include_durations=True)


if __name__ == "__main__":
    main()
