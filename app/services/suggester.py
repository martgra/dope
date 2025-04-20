import hashlib
import json
from pathlib import Path

from pydantic.json import pydantic_encoder

from app.agents.prompts import SUGGESTION_PROMPT
from app.models.domain import DocSuggestions

template = """

<{file_path}>
file_path: {file_path}

summary:
{summary}
</{file_path}>
"""


class DocChangeSuggester:
    """DocChangeSuggestor class."""

    def __init__(self, *, agent, suggestion_state_path: Path):
        self.agent = agent
        self.suggestion_state_path = Path(suggestion_state_path)

    @staticmethod
    def _prompt_formatter(state_dict: dict) -> str:
        formatted_prompt = ""

        for filepath, data in state_dict.items():
            formatted_prompt += template.format(
                file_path=filepath,
                summary=json.dumps(
                    data.get("summary"), indent=2, ensure_ascii=False, default=pydantic_encoder
                ),
            )
        return formatted_prompt

    def _check_get_state(self, state_hash: str):
        if not self.suggestion_state_path.is_file():
            return {}
        with self.suggestion_state_path.open() as file:
            state = json.load(file)
        if state_hash == state.get("hash"):
            return state
        else:
            return {}

    def get_state(self) -> DocSuggestions:
        """Return the suggested change state."""
        with self.suggestion_state_path.open() as file:
            return DocSuggestions.model_validate(json.load(file).get("suggestion"))

    def _get_state_hash(self, *, docs_change: dict, code_change: dict):
        return hashlib.md5(
            json.dumps(docs_change).encode("utf-8") + json.dumps(code_change).encode("utf-8")
        ).hexdigest()

    def _save_state(self, state):
        with self.suggestion_state_path.open("w") as file:
            json.dump(state, file, ensure_ascii=False, indent=True)

    def get_suggestions(self, *, docs_change, code_change):
        """Get suggestions how to update doc.

        Args:
            docs_change (_type_): _description_
            code_change (_type_): _description_

        Returns:
            _type_: _description_
        """
        state_hash = self._get_state_hash(code_change=code_change, docs_change=docs_change)
        suggestion_state = self._check_get_state(state_hash)
        if not suggestion_state:
            suggestion_state["hash"] = state_hash
            prompt = SUGGESTION_PROMPT.format(
                documentation=self._prompt_formatter(docs_change),
                code_changes=self._prompt_formatter(code_change),
            )
            suggestion = self.agent.run_sync(user_prompt=prompt).output
            suggestion_state["suggestion"] = suggestion.model_dump()
            self._save_state(suggestion_state)
        else:
            suggestion = DocSuggestions.model_validate(suggestion_state.get("suggestion"))

        return suggestion
