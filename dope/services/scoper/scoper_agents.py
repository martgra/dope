from functools import lru_cache

from pydantic_ai import Agent

from dope.core.settings import get_settings
from dope.llms.model_factory import get_model
from dope.models.domain.scope_template import AlignedScope, ProjectTier
from dope.services.scoper.prompts import (
    ALIGN_DOC_PROMPT,
    COMPLEXITY_DETERMINATION,
    CREATE_SCOPE_PROMPT,
)


@lru_cache(maxsize=1)
def get_project_complexity_agent() -> Agent[None, ProjectTier]:
    """Get the project complexity agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise RuntimeError("Agent configuration not found. Run 'dope config init' first.")
    agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=ProjectTier)

    @agent.system_prompt
    def _add_complexity_prompt() -> str:
        return COMPLEXITY_DETERMINATION

    return agent


@lru_cache(maxsize=1)
def get_scope_creator_agent() -> Agent[None, dict[str, str]]:
    """Get the scope creator agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise RuntimeError("Agent configuration not found. Run 'dope config init' first.")
    agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1"), output_type=dict[str, str])

    @agent.system_prompt
    def _add_scope_creator_prompt() -> str:
        return CREATE_SCOPE_PROMPT

    return agent


@lru_cache(maxsize=1)
def get_doc_aligner_agent() -> Agent[None, AlignedScope]:
    """Get the doc aligner agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise RuntimeError("Agent configuration not found. Run 'dope config init' first.")
    agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1"), output_type=AlignedScope)

    @agent.system_prompt
    def _fill_file_prompt() -> str:
        return ALIGN_DOC_PROMPT

    return agent
