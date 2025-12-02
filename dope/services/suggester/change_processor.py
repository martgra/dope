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

    @classmethod
    def format_changes_adaptive(  # pylint: disable=too-many-locals
        cls,
        state_dict: dict,
        include_metadata: bool = True,
        high_detail_threshold: float = 0.6,
        medium_detail_threshold: float = 0.3,
    ) -> str:
        """Format state with adaptive detail level based on relevance scores.

        Reduces token usage by pruning low-relevance details while preserving
        critical information for high-relevance changes.

        Detail levels:
        - High (relevance >= high_threshold): Full details including specific_changes
        - Medium (relevance >= medium_threshold): Functional impact only
        - Low (relevance < medium_threshold): Summary only

        Args:
            state_dict: Dictionary of file paths to state data
            include_metadata: Whether to include priority/magnitude metadata
            high_detail_threshold: Threshold for full detail inclusion (0-1)
            medium_detail_threshold: Threshold for medium detail inclusion (0-1)

        Returns:
            Formatted prompt string with adaptive detail levels

        Example:
            >>> formatted = ChangeProcessor.format_changes_adaptive(
            ...     code_state,
            ...     include_metadata=True,
            ...     high_detail_threshold=0.6,
            ...     medium_detail_threshold=0.3,
            ... )
        """
        processable = cls.filter_processable_files(state_dict)
        sorted_files = cls.sort_by_priority(processable)

        formatted_files = []
        for filepath, data in sorted_files:
            # Calculate combined relevance score
            priority = data.get("priority", "NORMAL")
            scope_relevance = data.get("scope_alignment", {}).get("max_relevance", 0.0)
            term_relevance = data.get("term_relevance", {}).get("match_count", 0)

            # Priority boost: HIGH gets +0.3, NORMAL gets 0
            priority_boost = 0.3 if priority == "HIGH" else 0.0

            # Term relevance boost: normalize by dividing by 20 (capped at 0.2)
            term_boost = min(term_relevance / 20.0, 0.2)

            combined_relevance = min(scope_relevance + priority_boost + term_boost, 1.0)

            # Determine detail level
            summary = data.get("summary")
            if not summary:
                continue

            # Prune summary based on relevance
            pruned_summary = cls._prune_summary_by_relevance(
                summary=summary,
                relevance=combined_relevance,
                high_threshold=high_detail_threshold,
                medium_threshold=medium_detail_threshold,
            )

            summary_str = json.dumps(
                pruned_summary,
                indent=2,
                ensure_ascii=False,
                default=pydantic_encoder,
            )

            if include_metadata:
                metadata = _build_metadata_dict(data)
                # Add combined relevance to metadata
                metadata["Combined Relevance"] = f"{combined_relevance:.2f}"
                formatted = format_file_content(
                    filepath, summary_str, tag_name=filepath, **metadata
                )
            else:
                formatted = format_file_content(filepath, summary_str, tag_name=filepath)

            formatted_files.append(formatted)

        return "\n".join(formatted_files)

    @staticmethod
    def _prune_summary_by_relevance(
        summary: dict | str,
        relevance: float,
        high_threshold: float,
        medium_threshold: float,
    ) -> dict | str:
        """Prune summary content based on relevance score.

        Args:
            summary: Summary dict or string to prune
            relevance: Combined relevance score (0-1)
            high_threshold: Threshold for full details
            medium_threshold: Threshold for medium details

        Returns:
            Pruned summary with appropriate detail level
        """
        # If summary is just a string, return as-is
        if isinstance(summary, str):
            return summary

        # If not a dict, return as-is
        if not isinstance(summary, dict):
            return summary

        # High relevance: keep everything
        if relevance >= high_threshold:
            return summary

        # Medium relevance: keep functional_impact, remove specific_changes
        if relevance >= medium_threshold:
            pruned = dict(summary)
            if "specific_changes" in pruned:
                # Keep summary but remove detailed specific changes
                change_count = len(pruned["specific_changes"])
                pruned["specific_changes"] = [
                    {
                        "name": "Details omitted",
                        "summary": f"{change_count} changes (medium relevance)",
                    }
                ]
            return pruned

        # Low relevance: keep only functional_impact
        pruned = {}
        if "functional_impact" in summary:
            pruned["functional_impact"] = summary["functional_impact"]
        if "programming_language" in summary:
            pruned["programming_language"] = summary["programming_language"]

        # Add note about pruning
        if "specific_changes" in summary:
            change_count = len(summary["specific_changes"])
            pruned["note"] = f"{change_count} specific changes omitted (low relevance)"

        return pruned
