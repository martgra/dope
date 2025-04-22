from pydantic_ai import Agent, RunContext

from app import settings
from app.agents.model_factory import get_model
from app.models.domain import DocSummary

PROMPT = """
of the file. You are not allowed to fill information you cannot find from the content of the file.
If you cannot fill information just reply with None.

The File content will be provided within:

<Content>
file content
</Content>
"""

model = get_model(settings.agent.provider, "gpt-4.1-mini")


doc_summarization_agent = Agent(model=model, output_type=DocSummary)


@doc_summarization_agent.system_prompt
def _add_summarization_prompt(ctx: RunContext[str]) -> str:
    return PROMPT
