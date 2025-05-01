from pydantic_ai import Agent

from app import settings
from app.llms.model_factory import get_model
from app.models.domain.scope_template import ProjectTier
from app.services.scoper.prompts import (
    ALIGN_DOC_PROMPT,
    COMPLEXITY_DETERMINATION,
    CREATE_SCOPE_PROMPT,
)

project_complexity_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1-mini"), output_type=ProjectTier
)


@project_complexity_agent.system_prompt
def _add_complexity_prompt() -> str:
    return COMPLEXITY_DETERMINATION


scope_creator_agent = Agent(
    model=get_model(settings.agent.provider, "gpt-4.1"), output_type=dict[str, str]
)


@scope_creator_agent.system_prompt
def _add_scope_creator_prompt() -> str:
    return CREATE_SCOPE_PROMPT


doc_aligner_agent = Agent(model=get_model(settings.agent.provider, "gpt-4.1"), output_type=str)


@doc_aligner_agent.system_prompt
def _fill_file_prompt() -> str:
    return ALIGN_DOC_PROMPT
