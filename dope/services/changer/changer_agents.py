from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent, RunContext

from dope import settings
from dope.consumers.git_consumer import GitConsumer
from dope.llms.model_factory import get_model
from dope.services.changer.prompts import CHANGE_DOC_PROMPT


@dataclass
class Deps:
    """Doc changer agent dependencies."""

    git_consumer: GitConsumer


changer_agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1"))


@changer_agent.tool
def get_code_file_content(_ctx: RunContext[Deps], code_filepath: str) -> str:
    """Return content of a code file.

    Args:
        code_filepath (str): Path to file.

    Returns:
        str: Content of code file.
    """
    print(f"Calling code tool for file {code_filepath}")
    if not Path(code_filepath).is_file():
        raise FileNotFoundError(code_filepath)
    content = _ctx.deps.git_consumer.get_full_content(file_path=code_filepath)
    return content


@changer_agent.system_prompt
def _add_summarization_prompt() -> str:
    return CHANGE_DOC_PROMPT
