"""Pydantic-AI agent that generates structured documentation-update suggestions."""

from pydantic_ai import Agent

from dope.core.loop_cache import loop_scoped_cache
from dope.exceptions import AgentNotConfiguredError
from dope.llms.model_factory import get_model
from dope.models.domain.documentation import DocSuggestions
from dope.models.settings import get_settings
from dope.services.suggester.prompts import SYSTEM_PROMPT


@loop_scoped_cache
def get_suggester_agent() -> Agent[None, DocSuggestions]:
    """Get the suggester agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    model = get_model(settings.agent.provider, "gpt-5.6-luna")
    agent = Agent(model=model, output_type=DocSuggestions)

    @agent.system_prompt
    def _add_summarization_prompt() -> str:
        return SYSTEM_PROMPT

    return agent
