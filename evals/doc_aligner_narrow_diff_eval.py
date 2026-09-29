"""Eval for the narrow-diff (v4-diff-narrow) doc_aligner variant.

Reuses every fixture and evaluator from :mod:`evals.doc_aligner_eval`.
The only differences are:

* Agent bound to ``NarrowEditedScope`` — schema forbids ``replace_range``,
  so the model can only ``insert_after`` or ``delete_range``.
* Prompt: ``scope.align_doc`` version ``v4-diff-narrow``.
* Task wrapper numbers input lines, applies edits, and returns an
  ``AlignedScope`` so shared evaluators plug in unchanged.

The head-to-head against the production full-content aligner is
:mod:`evals.doc_aligner_narrow_diff_ab`.

Run with::

    uv run python -m evals.doc_aligner_narrow_diff_eval
"""

from __future__ import annotations

import argparse
from typing import cast

from pydantic_ai import Agent

from dope.core.usage import UsageTracker
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.domain.scope import AlignedScope, NarrowEditedScope, apply_edits
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry
from evals.doc_aligner_diff_eval import _number_lines
from evals.doc_aligner_eval import (
    MAX_CONCURRENCY,
    DocAlignerInput,
    _usage_by_case,
    build_dataset,
)


def build_narrow_diff_aligner_agent(
    model_name: str | None = None,
) -> Agent[None, NarrowEditedScope]:
    """Construct a narrow-diff aligner agent bound to the v4-diff-narrow prompt."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    resolved_model = model_name or "gpt-5.6-terra"
    prompt = PromptRegistry.get("scope.align_doc", version="v4-diff-narrow")
    agent = Agent(
        model=get_model(settings.agent.provider, resolved_model),
        output_type=NarrowEditedScope,
    )

    @agent.system_prompt
    def _add_prompt() -> str:
        return prompt.template

    return agent


def make_run_narrow_diff_aligner(model_name: str | None = None):
    """Task factory: run narrow-diff aligner and reconstruct AlignedScope."""
    agent = build_narrow_diff_aligner_agent(model_name)
    user_prompt = PromptRegistry.get("scope.align_doc_diff_user_template", version="v1")

    async def _run(inputs: DocAlignerInput) -> AlignedScope:
        tracker = UsageTracker()
        prompt = user_prompt.render(
            scope=inputs.scope_summary,
            filepath=inputs.filepath,
            numbered_content=_number_lines(inputs.file_content),
        )
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        edited: NarrowEditedScope = cast(NarrowEditedScope, result.output)
        reconstructed = apply_edits(inputs.file_content, edited.edits)
        _usage_by_case[id(inputs)] = tracker.usage
        return AlignedScope(
            content=reconstructed,
            changes_in_other_files=edited.changes_in_other_files,
        )

    return _run


def main() -> None:
    """Build the dataset, run the narrow-diff aligner, print report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="override model (default: gpt-5.6-terra)")
    args = parser.parse_args()
    dataset = build_dataset()
    report = dataset.evaluate_sync(
        make_run_narrow_diff_aligner(args.model), max_concurrency=MAX_CONCURRENCY
    )
    report.print(include_input=False, include_output=False, include_durations=True)


if __name__ == "__main__":
    main()
