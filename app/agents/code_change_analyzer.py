from pydantic_ai import Agent

from app.agents.model_factory import get_model
from app.models.domain import CodeChanges

PROMPT = """
Summarize the git diff. The summarization will be used for to decide if the documentation ought to
be updated based on a git diff. The description needs to be detailed enough to understand what to change in the doc,
and why it is important.
"""  # noqa: E501

model = get_model("gpt-4.1-mini")

code_change_agent = Agent(model=model, output_type=CodeChanges)


@code_change_agent.system_prompt
def _add_summarization_prompt() -> str:
    return PROMPT
