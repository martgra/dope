from pydantic_ai import Agent

from app import settings
from app.agents.model_factory import get_model
from app.models.domain import DocSuggestions

PROMPT = """
Your role is to suggest changes to documentation that needs updating based on code changes.

Consider if the code change warrants a change in the documentation. We do not track updates -
the documentation always reflects the current state of the git repo.

We strive to add changes that either informs about how to use the application or how to get started developing.

We strive to not duplicate documentation across files.
"""  # noqa: E501

model = get_model(settings.agent.provider, "o4-mini")


agent = Agent(model=model, output_type=DocSuggestions)


@agent.system_prompt
def _add_summarization_prompt() -> str:
    return PROMPT
