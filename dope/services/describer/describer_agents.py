import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic_ai import Agent, RunContext

from dope.consumers.git_consumer import GitConsumer
from dope.exceptions import AgentNotConfiguredError, DocumentNotFoundError
from dope.llms.model_factory import get_model
from dope.models.domain.code import CodeChanges
from dope.models.domain.documentation import DocSummary
from dope.models.settings import get_settings
from dope.services.describer.prompts import CODE_DESCRIPTION_PROMPT, DOC_DESCRIPTION_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class Deps:
    """Agent dependencies."""

    consumer: GitConsumer


@lru_cache(maxsize=1)
def get_code_change_agent() -> Agent[Deps, CodeChanges]:
    """Get the code change agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(
        model=get_model(settings.agent.provider, "gpt-4.1-mini"),
        deps_type=Deps,
        output_type=CodeChanges,
    )

    @agent.system_prompt
    def _add_summarization_prompt() -> str:
        return CODE_DESCRIPTION_PROMPT

    @agent.tool
    def get_code_file_content(_ctx: RunContext[Deps], code_filepath: str) -> str:
        """Return content of a code file.

        Args:
            code_filepath (str): Path to a codefile in the repository.

        Returns:
            str: Content of code file.
        """
        logger.debug("Agent tool: fetching content for %s", code_filepath)
        if not Path(code_filepath).is_file():
            raise DocumentNotFoundError(code_filepath)
        content = _ctx.deps.consumer.get_full_content(file_path=code_filepath)
        return content

    return agent


@lru_cache(maxsize=1)
def get_doc_summarization_agent() -> Agent[None, DocSummary]:
    """Get the doc summarization agent (lazy-initialized and cached)."""
    settings = get_settings()
    if settings.agent is None:
        raise AgentNotConfiguredError()
    agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=DocSummary)

    @agent.system_prompt
    def _add_summarization_prompt() -> str:
        return DOC_DESCRIPTION_PROMPT

    return agent
