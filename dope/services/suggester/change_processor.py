import json

from pydantic.json import pydantic_encoder

from dope.core.prompts import format_file_content


def _get_significance_label(magnitude: float) -> str:
    """Convert magnitude score to human-readable significance."""
    if magnitude > 0.7:
        return "major"
    elif magnitude > 0.4:
        return "medium"
    return "minor"


def _build_metadata_dict(data: dict) -> dict[str, str]:
    """Extract metadata from file data for prompt inclusion.

    Args:
        data: File state data with priority and metadata.

    Returns:
        Dictionary of metadata key-value pairs for prompt.
    """
    result: dict[str, str] = {}

    priority = data.get("priority", "NORMAL")
    result["Priority"] = priority

    metadata = data.get("metadata", {})
    magnitude = metadata.get("magnitude", 0.0)
    lines_added = metadata.get("lines_added", 0)
    lines_deleted = metadata.get("lines_deleted", 0)

    if magnitude > 0:
        significance = _get_significance_label(magnitude)
        result["Change Magnitude"] = f"{magnitude:.2f} (significance: {significance})"

    if lines_added > 0 or lines_deleted > 0:
        result["Lines Changed"] = f"+{lines_added} -{lines_deleted}"

    # Add scope alignment if available
    scope_alignment = data.get("scope_alignment")
    if scope_alignment:
        max_relevance = scope_alignment.get("max_relevance", 0.0)
        category = scope_alignment.get("category")
        relevant_sections = scope_alignment.get("relevant_sections", [])

        if max_relevance > 0:
            result["Scope Relevance"] = f"{max_relevance:.2f}"

        if category:
            result["Category"] = category

        if relevant_sections:
            # Show top 3 affected docs
            affected_docs = [f"{s['doc']}.{s['section']}" for s in relevant_sections[:3]]
            result["Affects Docs"] = ", ".join(affected_docs)

    return result


class ChangeProcessor:
    """Handles filtering, sorting, and formatting of changes."""

    @staticmethod
    def filter_processable_files(state_dict: dict) -> dict:
        """Filter out skipped files and return only processable changes."""
        processable = {}
        for filepath, data in state_dict.items():
            if data.get("skipped"):
                continue
            if not data.get("summary"):
                continue
            processable[filepath] = data
        return processable

    @staticmethod
    def sort_by_priority(state_dict: dict) -> list[tuple[str, dict]]:
        """Sort files by priority (HIGH first, then NORMAL)."""
        items = list(state_dict.items())

        def priority_key(item):
            filepath, data = item
            priority = data.get("priority", "NORMAL")
            magnitude = data.get("metadata", {}).get("magnitude", 0.0)

            # Sort order: HIGH priority first, then by magnitude (descending)
            if priority == "HIGH":
                return (0, -magnitude)
            else:
                return (1, -magnitude)

        return sorted(items, key=priority_key)

    @classmethod
    def format_changes_for_prompt(cls, state_dict: dict, include_metadata: bool = True) -> str:
        """Format state into prompt string.

        Args:
            state_dict: Dictionary of file paths to state data.
            include_metadata: Whether to include priority/magnitude metadata.

        Returns:
            Formatted prompt string with all file summaries.
        """
        processable = cls.filter_processable_files(state_dict)
        sorted_files = cls.sort_by_priority(processable)

        formatted_files = []
        for filepath, data in sorted_files:
            summary = json.dumps(
                data.get("summary"),
                indent=2,
                ensure_ascii=False,
                default=pydantic_encoder,
            )

            if include_metadata:
                metadata = _build_metadata_dict(data)
                formatted = format_file_content(filepath, summary, tag_name=filepath, **metadata)
            else:
                formatted = format_file_content(filepath, summary, tag_name=filepath)

            formatted_files.append(formatted)

        return "\n".join(formatted_files)
