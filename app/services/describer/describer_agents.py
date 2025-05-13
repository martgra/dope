from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent, RunContext

from app import get_settings
from app.consumers.git_consumer import GitConsumer
from app.llms.model_factory import get_model
from app.models.domain.code import CodeChanges
from app.models.domain.doc import DocSummary
from app.services.describer.prompts import CODE_DESCRIPTION_PROMPT, DOC_DESCRIPTION_PROMPT

settings = get_settings()


@dataclass
class Deps:
    """Agent dependencies."""

    consumer: GitConsumer


code_change_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1-mini"),
    output_type=CodeChanges,
    deps_type=Deps,
)


@code_change_agent.system_prompt
def _add_summarization_prompt() -> str:
    return CODE_DESCRIPTION_PROMPT


@code_change_agent.tool
def get_code_file_content(_ctx: RunContext[Deps], code_filepath: str) -> str:
    """Return content of a code file.

    Args:
        code_filepath (str): Path to a codefile in the repository.

    Returns:
        str: Content of code file.
    """
    print(f"Calling code tool for file {code_filepath}")
    if not Path(code_filepath).is_file():
        raise FileNotFoundError(code_filepath)
    content = _ctx.deps.git_consumer.get_full_content(file_path=code_filepath)
    return content


doc_summarization_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=DocSummary
)


@doc_summarization_agent.system_prompt
def _add_summarization_prompt(ctx: RunContext[str]) -> str:
    return DOC_DESCRIPTION_PROMPT
