from pydantic_ai import Agent, RunContext

from app import settings
from app.llms.model_factory import get_model
from app.models.domain.code import CodeChanges
from app.models.domain.doc import DocSummary
from app.services.describer.prompts import CODE_DESCRIPTION_PROMPT, DOC_DESCRIPTION_PROMPT

code_change_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=CodeChanges
)


@code_change_agent.system_prompt
def _add_summarization_prompt() -> str:
    return CODE_DESCRIPTION_PROMPT


doc_summarization_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=DocSummary
)


@doc_summarization_agent.system_prompt
def _add_summarization_prompt(ctx: RunContext[str]) -> str:
    return DOC_DESCRIPTION_PROMPT
