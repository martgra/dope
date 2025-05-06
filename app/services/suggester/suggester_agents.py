from pydantic_ai import Agent

from app import settings
from app.llms.model_factory import get_model
from app.models.domain.doc import DocSuggestions
from app.services.suggester.prompts import SUGGESTION_PROMPT

model = get_model(settings.agent.provider, "o4-mini")


suggester_agent = Agent(model=model, output_type=DocSuggestions)


@suggester_agent.system_prompt
def _add_summarization_prompt() -> str:
    return SUGGESTION_PROMPT
