"""Pydantic-AI agents for project scoping: complexity, structure, alignment."""

# pylint: disable=duplicate-code

from pydantic_ai import Agent

from dope.core.loop_cache import loop_scoped_cache
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.domain.scope import AlignedScope
from dope.models.enums import ProjectTier
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry


@loop_scoped_cache
def get_project_complexity_agent() -> Agent[None, ProjectTier]:
    """Get the project complexity agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(model=get_model(settings.agent.provider, "gpt-5.6-luna"), output_type=ProjectTier)

    @agent.system_prompt
    def _add_complexity_prompt() -> str:
        return PromptRegistry.get("scope.complexity").template

    return agent


@loop_scoped_cache
def get_scope_creator_agent() -> Agent[None, dict[str, str]]:
    """Get the scope creator agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(
        model=get_model(settings.agent.provider, "gpt-5.6-luna"),
        output_type=dict[str, str],
    )

    @agent.system_prompt
    def _add_scope_creator_prompt() -> str:
        return PromptRegistry.get("scope.creator").template

    return agent


@loop_scoped_cache
def get_doc_aligner_agent() -> Agent[None, AlignedScope]:
    """Get the doc aligner agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(
        model=get_model(settings.agent.provider, "gpt-5.6-terra"),
        output_type=AlignedScope,
    )

    @agent.system_prompt
    def _fill_file_prompt() -> str:
        return PromptRegistry.get("scope.align_doc").template

    return agent
