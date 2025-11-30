import json

from pydantic.json import pydantic_encoder

from dope.core.usage import UsageTracker
from dope.models.domain.doc import SuggestedChange
from dope.services.changer.changer_agents import Deps, get_changer_agent
from dope.services.changer.prompts import ADD_DOC_USER_PROMPT, CHANGE_DOC_USER_PROMPT


class DocsChanger:
    """DocChanger class."""

    def __init__(self, *, docs_consumer, git_consumer, usage_tracker: UsageTracker | None = None):
        """Initialize DocChanger.

        Args:
            docs_consumer: Consumer for documentation files
            git_consumer: Consumer for Git operations
            usage_tracker: Optional usage tracker for LLM token tracking
        """
        self.docs_consumer = docs_consumer
        self.git_consumer = git_consumer
        self._agent = None
        self.usage_tracker = usage_tracker or UsageTracker()

    @property
    def agent(self):
        """Lazy-load the agent only when needed."""
        if self._agent is None:
            self._agent = get_changer_agent()
        return self._agent

    def _change_prompt(self, docs_content: str, suggested_change: SuggestedChange):
        return CHANGE_DOC_USER_PROMPT.format(
            doc_path=suggested_change.documentation_file_path,
            doc_content=docs_content,
            changes_content=json.dumps(
                suggested_change.suggested_changes, indent=2, default=pydantic_encoder
            ),
        )

    def _add_prompt(self, suggested_change: SuggestedChange):
        return ADD_DOC_USER_PROMPT.format(
            doc_path=suggested_change.documentation_file_path,
            changes_content=json.dumps(
                suggested_change.suggested_changes, indent=2, default=pydantic_encoder
            ),
        )

    def apply_suggestion(self, suggested_change: SuggestedChange):
        """Apply suggestions to documentation files.

        Args:
            suggested_change (SuggestedChange): Suggestions.

        Returns:
            dict[str, str]: Dict of file paths and content of doc files..
        """
        content = self.docs_consumer.get_content(suggested_change.documentation_file_path)
        prompt = ""
        if suggested_change.change_type == "change_existing":
            prompt = self._change_prompt(content, suggested_change)
        if suggested_change.change_type == "add":
            prompt = self._add_prompt(suggested_change)
        if suggested_change.change_type == "delete":
            prompt = "Return DELETE as the suggestion is to remove the file."

        content = self.agent.run_sync(
            user_prompt=prompt,
            deps=Deps(git_consumer=self.git_consumer),
            usage=self.usage_tracker.usage,
        ).output
        return suggested_change.documentation_file_path, content
