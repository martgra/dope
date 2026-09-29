"""Cost + accuracy + latency eval for the doc_aligner agent.

Fixtures live in ``evals/fixtures/doc_aligner/*.yaml``. Each holds:

* ``scope_summary`` — a short YAML-like summary of the scope the
  aligner should conform to. Full ScopeTemplate objects run to
  hundreds of lines of section metadata; the aligner's system prompt
  only really uses the description of each doc and its sections, so we
  pass a slimmed representation to keep fixtures readable
* ``filepath`` — the target doc path
* ``file_content`` — current markdown content the aligner will rewrite

Run with::

    uv run python -m evals.doc_aligner_eval

Requires an OpenAI/Azure token in ``.env``. Uses whatever tier
:func:`get_doc_aligner_agent` is currently pinned to (``gpt-5.6-sol`` at
time of writing).

Scoring uses :class:`LLMJudge` with four rubrics that mirror the
aligner's contract: it should incorporate the scope's expected
sections, preserve unrelated existing content, avoid inventing facts,
and produce valid markdown. Also captures per-case cost/tokens/latency.
"""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, LLMJudge

from dope.core.usage import UsageTracker
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.domain.scope import AlignedScope
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry
from dope.services.scoper.scoper_agents import get_doc_aligner_agent

FIXTURES = Path(__file__).parent / "fixtures" / "doc_aligner"
MAX_CONCURRENCY = 2
JUDGE_MODEL_NAME = "gpt-5.6-terra"

_usage_by_case: dict[int, RunUsage] = {}


def _build_judge_model():
    """Construct the LLM-as-judge model through dope's provider factory."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    return get_model(settings.agent.provider, JUDGE_MODEL_NAME)


class DocAlignerInput(BaseModel):
    """Bundle of scope summary + target filepath + existing file content.

    Modeled as a pydantic ``BaseModel`` so :class:`LLMJudge`
    (with ``include_input=True``) can serialize the fields into the
    judge prompt as JSON — a plain object would render as
    ``<DocAlignerInput object at 0x...>`` and hide the very context the
    rubrics compare against. See changer_eval.py for the same lesson.
    """

    scope_summary: str
    filepath: str
    file_content: str
    must_preserve: list[str] = []
    """Substrings from the existing file that must survive verbatim in
    the rewrite. Same contract as :class:`ChangerInput.must_preserve`."""


class CostMetrics(Evaluator[DocAlignerInput, AlignedScope]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(
        self, ctx: EvaluatorContext[DocAlignerInput, AlignedScope, dict]
    ) -> dict[str, float]:
        """Return cost/tokens/requests captured by the task wrapper."""
        usage = _usage_by_case.get(id(ctx.inputs))
        if usage is None:
            return {}
        return {
            "cost_usd": float(usage.cost or 0),
            "tokens": float(usage.total_tokens or 0),
            "requests": float(usage.requests or 0),
        }


class CrossFileChangesCount(Evaluator[DocAlignerInput, AlignedScope]):
    """Emit the count of ``changes_in_other_files`` for observability."""

    def evaluate(
        self, ctx: EvaluatorContext[DocAlignerInput, AlignedScope, dict]
    ) -> dict[str, float]:
        """Return the count of cross-file change suggestions."""
        return {"cross_file_changes": float(len(ctx.output.changes_in_other_files))}


class ContentSimilarity(Evaluator[DocAlignerInput, AlignedScope]):
    """Char-level similarity between the existing file and the rewrite.

    ``difflib.SequenceMatcher(input, output.content).ratio()`` — higher
    means less over-rewriting. See :class:`evals.changer_eval.ContentSimilarity`.
    """

    def evaluate(
        self, ctx: EvaluatorContext[DocAlignerInput, AlignedScope, dict]
    ) -> dict[str, float]:
        """Return similarity + char-delta ratios."""
        inp = ctx.inputs.file_content
        out = ctx.output.content or ""
        similarity = difflib.SequenceMatcher(None, inp, out).ratio()
        char_delta = abs(len(out) - len(inp)) / max(len(inp), 1)
        return {"content_similarity": similarity, "char_delta_ratio": char_delta}


class PreservedSpecifics(Evaluator[DocAlignerInput, AlignedScope]):
    """Fraction of ``must_preserve`` substrings that survive verbatim."""

    def evaluate(
        self, ctx: EvaluatorContext[DocAlignerInput, AlignedScope, dict]
    ) -> dict[str, float]:
        """Return the retention ratio for declared must-preserve tokens."""
        specifics = ctx.inputs.must_preserve
        if not specifics:
            return {"preserved_specifics": 1.0}
        out = ctx.output.content or ""
        kept = sum(1 for s in specifics if s in out)
        return {"preserved_specifics": kept / len(specifics)}


_JUDGE_RUBRICS = {
    "incorporates_scope": (
        "The rewritten `output.content` must contain the sections that the "
        "fixture's `scope_summary` says this doc should have. Score 1 if "
        "every scope-required section appears (heading present, roughly "
        "correct place); 0 if any scope-required section is missing."
    ),
    "preserves_relevant_content": (
        "Existing content that IS in scope for this doc (per `scope_summary`) "
        "must be preserved. It is fine to reword lightly or reorder to match "
        "the scope's section order, but factual content that belongs in this "
        "doc should not be silently dropped. Score 1 when in-scope existing "
        "content is present in the rewrite; 0 when in-scope content was lost."
    ),
    "no_hallucinations": (
        "The rewrite must not invent facts, commands, function names, or "
        "code references that are not present in either the existing file "
        "content or the scope summary. Placeholders like TODO or bullet "
        "stubs are acceptable when the scope calls for a section the "
        "existing file lacked. Score 1 when the rewrite is grounded in the "
        "sources; 0 when it fabricates concrete claims."
    ),
    "valid_markdown": (
        "The `output.content` must be well-formed Markdown: balanced code "
        "fences, sensible heading levels, no stray XML/YAML fragments or "
        "leaked system-prompt chatter. Score 1 when the output could be "
        "written to disk as-is; 0 for malformed markdown."
    ),
    "minimal_change": (
        "Compare the rewritten `output.content` to the ORIGINAL "
        "`file_content` in the input. The aligner should scaffold "
        "sections the scope requires when they are missing, and it may "
        "reorder to match the scope's section order — but it must NOT: "
        "rephrase unrelated in-scope sentences, expand terse content the "
        "scope did not ask to expand, invent new subsections beyond what "
        "the scope specifies, or 'improve' wording that was already fine. "
        "Score 1 for a minimal alignment; 0 when the model rewrote "
        "content that the scope did not require touching."
    ),
}


def _load_case(path: Path) -> Case[DocAlignerInput, None, dict]:
    data = yaml.safe_load(path.read_text())
    inputs = DocAlignerInput(
        scope_summary=data["scope_summary"],
        filepath=data["filepath"],
        file_content=data["file_content"],
        must_preserve=data.get("must_preserve", []),
    )
    return Case(
        name=data["name"],
        inputs=inputs,
        expected_output=None,
        metadata={"description": data.get("description", "").strip()},
    )


def build_dataset() -> Dataset[DocAlignerInput, None, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    judge_model = _build_judge_model()
    evaluators = [
        LLMJudge(rubric=rubric, model=judge_model, include_input=True)
        for rubric in _JUDGE_RUBRICS.values()
    ]
    evaluators.extend(
        [CrossFileChangesCount(), ContentSimilarity(), PreservedSpecifics(), CostMetrics()]
    )
    return Dataset(name="doc_aligner", cases=cases, evaluators=evaluators)


def build_doc_aligner_agent(
    model_name: str | None = None, system_prompt: str | None = None
) -> Agent[None, AlignedScope]:
    """Construct a doc_aligner agent for the given model name (and optional prompt)."""
    if model_name is None and system_prompt is None:
        return get_doc_aligner_agent()
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    resolved_model = model_name or "gpt-5.6-sol"
    resolved_prompt = system_prompt or PromptRegistry.get("scope.align_doc").template
    agent = Agent(
        model=get_model(settings.agent.provider, resolved_model),
        output_type=AlignedScope,
    )

    @agent.system_prompt
    def _add_prompt() -> str:
        return resolved_prompt

    return agent


def _build_user_prompt(inputs: DocAlignerInput) -> str:
    """Mirror the shape of :class:`ScopeService`'s change_file user template."""
    return PromptRegistry.get("scope.change_file_user_template").render(
        scope=inputs.scope_summary,
        filepath=inputs.filepath,
        file_content=inputs.file_content,
    )


def make_run_doc_aligner(model_name: str | None = None, system_prompt: str | None = None):
    """Factory that binds a model + optional prompt to the task wrapper."""
    agent = build_doc_aligner_agent(model_name, system_prompt)

    async def _run(inputs: DocAlignerInput) -> AlignedScope:
        tracker = UsageTracker()
        prompt = _build_user_prompt(inputs)
        result = await agent.run(user_prompt=prompt, usage=tracker.usage)
        _usage_by_case[id(inputs)] = tracker.usage
        return result.output

    return _run


def main() -> None:
    """Build the dataset, run the doc_aligner on every fixture, print report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="override model")
    args = parser.parse_args()
    dataset = build_dataset()
    report = dataset.evaluate_sync(
        make_run_doc_aligner(args.model), max_concurrency=MAX_CONCURRENCY
    )
    report.print(include_input=False, include_output=False, include_durations=True)


if __name__ == "__main__":
    main()
