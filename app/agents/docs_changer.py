from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent, RunContext

from app.agents.model_factory import get_model
from app.consumers.git_consumer import GitConsumer

PROMPT = """
You are tasked to change the documentation for this application.

The scope of the documentation is to:
1. Give users a functional guide to how to use the application.
2. Give users a exemplified guide on how to set up the application.
3. Give users a understanding of how the application can be configured.

WORKFLOW
1. Read the documentation the user provides carefully. Make sure to understand it in context of the scope.
2. Review the suggested changes provided by the user.
3. Use the provided tool to get content of the code files.
4. Output only the full new documentation files.

TOOLS:
get_code_file_content: Load the content of code files as they are now to see specific details.
"""  # noqa: E501


@dataclass
class Deps:
    """Doc changer agent dependencies."""

    git_consumer: GitConsumer


model = get_model("gpt-4.1")


agent = Agent(model=model)


@agent.tool
def get_code_file_content(ctx: RunContext[Deps], code_filepath: str) -> str:
    """Return content of a code file.

    Args:
        code_filepath (str): Path to file.

    Returns:
        str: Content of code file.
    """
    print(f"Calling code tool for file {code_filepath}")
    if not Path(code_filepath).is_file():
        raise FileNotFoundError(code_filepath)
    content = ctx.deps.git_consumer.get_full_content(file_path=code_filepath)
    print(content)
    return content


@agent.system_prompt
def _add_summarization_prompt() -> str:
    return PROMPT
