import hashlib
import json
from pathlib import Path

from app.consumers.base import BaseConsumer
from app.core.context import UsageContext
from app.services.describer.prompts import SUMMARIZATION_TEMPLATE


class Scanner:
    """Scanner service."""

    def __init__(self, consumer: BaseConsumer, agent, state_filepath: Path = None):
        self.agent = agent
        self.consumer = consumer
        self.state_filepath = state_filepath

    def _compute_hash(self, file_path: Path) -> str:
        return hashlib.md5(self.consumer.get_content(file_path).encode("utf-8")).hexdigest()

    def _scan_files(self) -> dict:
        file_hashes = {}
        for file_path in self.consumer.discover_files():
            file_hash = self._compute_hash(file_path)
            file_hashes[str(file_path)] = {"hash": file_hash}
        return file_hashes

    def load_state(self) -> dict:
        """Load the scanner state."""
        if self.state_filepath.exists():
            with self.state_filepath.open("r") as f:
                return json.load(f)
        return {}

    def save_state(self, state: dict):
        """Save the state of the scanner."""
        self.state_filepath.parent.mkdir(parents=True, exist_ok=True)
        with self.state_filepath.open("w") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)

    def _update_state(self, new_items: dict, current_state: dict) -> dict:
        for key in list(current_state.keys()):
            if key not in new_items:
                del current_state[key]
        for key, value in new_items.items():
            if key not in current_state or current_state[key]["hash"] != value["hash"]:
                current_state[key] = {"hash": value["hash"], "summary": None}
        return current_state

    def scan(self) -> dict:
        """Perform scanning by updating the state based on discovered files and their hashes."""
        old_state = self.load_state()
        new_items = self._scan_files()
        updated_state = self._update_state(new_items, old_state)
        self.save_state(updated_state)
        return updated_state

    def get_state(self) -> dict:
        """Return state."""
        return self.load_state()

    def describe(self, file_path, state_item) -> dict:
        """For each file with a missing summary, generate one using the agent."""
        if not state_item["summary"]:
            content = self.consumer.get_content(self.consumer.root_path / file_path)
            prompt = SUMMARIZATION_TEMPLATE.format(file_path=file_path, content=content)
            try:
                state_item["summary"] = self.agent.run_sync(
                    user_prompt=prompt,
                    usage=UsageContext().usage,
                ).data.model_dump()
            except Exception:
                state_item["summary"] = None
        return state_item
