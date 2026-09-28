"""Cost + accuracy + latency eval for the changer agent.

Fixtures live in ``evals/fixtures/changer/*.yaml``. Each holds:

* ``existing_doc`` — ``{path, content}`` of the doc the changer must rewrite
* ``change_type`` — ``change_existing`` / ``add`` (``delete`` skipped: the
  production changer returns the string "DELETE" for that path)
* ``suggestions`` — list of ``{suggestion, code_references}`` items
  (matching :class:`ChangeSuggestion`) that the changer must incorporate
* ``code_files`` — mapping of path → content served through a fake
  git-consumer to the changer's ``get_code_file_content`` tool

Run with::

    uv run python -m evals.changer_eval

Requires an OpenAI/Azure token in ``.env``. Uses whatever tier
:func:`get_changer_agent` is currently pinned to (gpt-5.6-sol at time of
writing).

Scoring: output is prose (full markdown rewrite), so we use pydantic-evals
:class:`LLMJudge` with narrow rubrics for the four axes that matter for a
doc rewrite: incorporates the suggestion, preserves the original
structure, avoids hallucinated content, and is well-formed markdown. The
judge model defaults to ``gpt-5.6-terra`` (neither the baseline nor the
usual challengers, avoiding self-judging bias).

Cost/token/request counts are captured per case in the same side-channel
pattern as the other eval suites.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, LLMJudge

from dope.core.usage import UsageTracker
from dope.exceptions import AgentNotConfiguredError, DocumentNotFoundError
from dope.llms.model_factory import get_model
from dope.models.domain.documentation import ChangeSuggestion
from dope.models.enums import ChangeType
from dope.models.settings import get_settings
from dope.services.changer.changer_agents import Deps, get_changer_agent
from dope.services.changer.prompts import (
    ADD_DOC_USER_PROMPT,
    CHANGE_DOC_PROMPT,
    CHANGE_DOC_USER_PROMPT,
)

FIXTURES = Path(__file__).parent / "fixtures" / "changer"
MAX_CONCURRENCY = 2
JUDGE_MODEL_NAME = "gpt-5.6-terra"

_usage_by_case: dict[int, RunUsage] = {}


def _build_judge_model():
    """Construct the LLM-as-judge model through dope's provider factory.

    Passing the raw string ``"openai:gpt-5.6-terra"`` makes pydantic-ai
    build a fresh OpenAIProvider that reads ``OPENAI_API_KEY``; dope stores
    its token as ``agent__TOKEN`` via pydantic-settings, so we route the
    judge through :func:`get_model` to reuse the same credentials as
    production.
    """
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    return get_model(settings.agent.provider, JUDGE_MODEL_NAME)


class ChangerInput(BaseModel):
    """Bundle of existing doc + suggestions + fake code-file corpus.

    Modeled as a pydantic ``BaseModel`` rather than a plain class so that
    :class:`LLMJudge` (with ``include_input=True``) can serialize the
    original doc and suggestions into the judge prompt as JSON — a plain
    object would render as ``<ChangerInput object at 0x...>`` and hide
    the very context the rubrics compare against.
    """

    existing_doc_path: str
    existing_doc_content: str
    change_type: ChangeType
    suggestions: list[ChangeSuggestion]
    code_files: dict[str, str]

    model_config = {"arbitrary_types_allowed": True}


class _FakeGitConsumer:
    """Serves fixture code content for the changer's tool calls."""

    def __init__(self, files: dict[str, str]) -> None:
        """Store the (path -> content) map."""
        self._files = files

    def get_full_content(self, file_path: str) -> str:
        """Return the fixture content for ``file_path`` or a sentinel."""
        if file_path not in self._files:
            raise DocumentNotFoundError(file_path)
        return self._files[file_path]


class _FakeDocsConsumer:
    """Serves the fixture's existing_doc content to the changer service."""

    def __init__(self, path: str, content: str) -> None:
        """Store the single (path, content) the fixture describes."""
        self._path = path
        self._content = content

    def get_content(self, file_path):
        """Return the fixture doc bytes for the changer to rewrite."""
        return self._content.encode("utf-8")


class CostMetrics(Evaluator[ChangerInput, str]):
    """Read usage captured by the task wrapper and emit as evaluator scores."""

    def evaluate(self, ctx: EvaluatorContext[ChangerInput, str, dict]) -> dict[str, float]:
        """Return cost/tokens/requests captured by the task wrapper."""
        usage = _usage_by_case.get(id(ctx.inputs))
        if usage is None:
            return {}
        return {
            "cost_usd": float(usage.cost or 0),
            "tokens": float(usage.total_tokens or 0),
            "requests": float(usage.requests or 0),
        }


_JUDGE_RUBRICS = {
    "incorporates_suggestion": (
        "The output must incorporate the change described in the fixture's "
        "`suggestions` list. Check that the specific addition, modification, "
        "or removal named in the suggestion appears in the rewritten doc in "
        "a semantically-correct place. Score 1 if all suggestions were "
        "clearly incorporated; 0 if any material suggestion is missing or "
        "incorrectly applied."
    ),
    "preserves_structure": (
        "The output must preserve the existing document's headings, section "
        "order, and unrelated content. Reordering unrelated bullets, dropping "
        "unrelated sections, or renaming untouched headings should score 0. "
        "Score 1 when structure changes are limited to what the suggestions "
        "explicitly require."
    ),
    "no_hallucinations": (
        "The output must not invent facts, commands, function names, or code "
        "references that are not present in either the existing doc or the "
        "fixture's `code_files`. Score 1 if the rewrite only mentions things "
        "grounded in the sources; 0 if the model fabricates a non-existent "
        "API, wrong signature, invented CLI flag, or bogus example."
    ),
    "valid_markdown": (
        "The output must be well-formed Markdown: balanced code fences, "
        "reasonable heading levels, no stray XML/YAML fragments, no leaked "
        "system-prompt or tool-call chatter. Score 1 when the output could be "
        "written to disk as-is; 0 for malformed markdown."
    ),
}


def _load_case(path: Path) -> Case[ChangerInput, None, dict]:
    data = yaml.safe_load(path.read_text())
    inputs = ChangerInput(
        existing_doc_path=data["existing_doc"]["path"],
        existing_doc_content=data["existing_doc"]["content"],
        change_type=ChangeType(data["change_type"]),
        suggestions=[ChangeSuggestion(**s) for s in data.get("suggestions", [])],
        code_files=data.get("code_files", {}),
    )
    # Force id() stability for the CostMetrics side channel: the task
    # wrapper writes _usage_by_case[id(inputs)] and the evaluator reads
    # by the same key.  With BaseModel, ctx.inputs is the same object
    # the wrapper received.
    return Case(
        name=data["name"],
        inputs=inputs,
        expected_output=None,
        metadata={"description": data.get("description", "").strip()},
    )


def build_dataset() -> Dataset[ChangerInput, None, dict]:
    """Assemble a Dataset from every YAML fixture under ``FIXTURES``."""
    cases = [_load_case(p) for p in sorted(FIXTURES.glob("*.yaml"))]
    judge_model = _build_judge_model()
    evaluators = [
        LLMJudge(rubric=rubric, model=judge_model, include_input=True)
        for rubric in _JUDGE_RUBRICS.values()
    ]
    evaluators.append(CostMetrics())
    return Dataset(name="changer", cases=cases, evaluators=evaluators)


def build_changer_agent(model_name: str | None = None) -> Agent:
    """Construct a changer agent for the given model name.

    Passing ``None`` returns the production factory's agent (currently
    ``gpt-5.6-sol``); any other model name builds a fresh Agent with the
    same tool + system prompt but a different underlying model. Used by
    :mod:`evals.changer_ab` to compare model tiers on the same fixtures.
    """
    if model_name is None:
        return get_changer_agent()
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(
        model=get_model(settings.agent.provider, model_name),
        deps_type=Deps,
    )

    @agent.tool
    def get_code_file_content(ctx, code_filepath: str) -> str:
        """Return content of a code file (fixture-served during evals)."""
        return ctx.deps.git_consumer.get_full_content(file_path=code_filepath)

    @agent.system_prompt
    def _add_prompt() -> str:
        return CHANGE_DOC_PROMPT

    return agent


def _build_user_prompt(inputs: ChangerInput) -> str:
    """Mirror :class:`DocsChanger` prompt shape without its sync wrapper."""
    changes_content = json.dumps(
        [s.model_dump() for s in inputs.suggestions], indent=2, default=pydantic_encoder
    )
    if inputs.change_type == ChangeType.CHANGE:
        return CHANGE_DOC_USER_PROMPT.format(
            doc_path=inputs.existing_doc_path,
            doc_content=inputs.existing_doc_content,
            changes_content=changes_content,
        )
    if inputs.change_type == ChangeType.ADD:
        return ADD_DOC_USER_PROMPT.format(
            doc_path=inputs.existing_doc_path,
            changes_content=changes_content,
        )
    return "Return DELETE as the suggestion is to remove the file."


def make_run_changer(model_name: str | None = None):
    """Factory that binds a model to the task wrapper used by evaluate_sync."""
    agent = build_changer_agent(model_name)

    async def _run(inputs: ChangerInput) -> str:
        tracker = UsageTracker()
        prompt = _build_user_prompt(inputs)
        result = await agent.run(
            user_prompt=prompt,
            deps=Deps(git_consumer=_FakeGitConsumer(inputs.code_files)),
            usage=tracker.usage,
        )
        _usage_by_case[id(inputs)] = tracker.usage
        return result.output

    return _run


def main() -> None:
    """Build the dataset, run the changer agent on every fixture, print report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="override model (default: production)")
    args = parser.parse_args()
    dataset = build_dataset()
    report = dataset.evaluate_sync(make_run_changer(args.model), max_concurrency=MAX_CONCURRENCY)
    report.print(include_input=False, include_output=False, include_durations=True)


if __name__ == "__main__":
    main()
