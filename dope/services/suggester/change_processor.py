"""Filtering and prompt formatting helpers for summarized changes."""

import json

from pydantic.json import pydantic_encoder

from dope.core.prompts import format_file_content


def _get_significance_label(magnitude: float) -> str:
    """Convert magnitude score to a human-readable significance label."""
    if magnitude > 0.7:
        return "major"
    if magnitude > 0.4:
        return "medium"
    return "minor"


def _build_metadata_dict(data: dict) -> dict[str, str]:
    """Extract prompt metadata from a file state entry."""
    result = {"Priority": data.get("priority", "NORMAL")}
    metadata = data.get("metadata", {})
    magnitude = metadata.get("magnitude", 0.0)
    lines_added = metadata.get("lines_added", 0)
    lines_deleted = metadata.get("lines_deleted", 0)

    if magnitude > 0:
        result["Change Magnitude"] = (
            f"{magnitude:.2f} (significance: {_get_significance_label(magnitude)})"
        )
    if lines_added > 0 or lines_deleted > 0:
        result["Lines Changed"] = f"+{lines_added} -{lines_deleted}"

    scope_alignment = data.get("scope_alignment")
    if not scope_alignment:
        return result
    if scope_alignment.get("max_relevance", 0.0) > 0:
        result["Scope Relevance"] = f"{scope_alignment['max_relevance']:.2f}"
    if category := scope_alignment.get("category"):
        result["Category"] = category
    if sections := scope_alignment.get("relevant_sections", []):
        result["Affects Docs"] = ", ".join(
            f"{section['doc']}.{section['section']}" for section in sections[:3]
        )
    return result


def filter_processable_files(state_dict: dict) -> dict:
    """Return non-skipped files that have summaries."""
    return {
        file_path: data
        for file_path, data in state_dict.items()
        if not data.get("skipped") and data.get("summary")
    }


def sort_by_priority(state_dict: dict) -> list[tuple[str, dict]]:
    """Sort files by HIGH priority first, then descending change magnitude."""
    return sorted(
        state_dict.items(),
        key=lambda item: (
            0 if item[1].get("priority", "NORMAL") == "HIGH" else 1,
            -item[1].get("metadata", {}).get("magnitude", 0.0),
        ),
    )


def format_changes_for_prompt(state_dict: dict, include_metadata: bool = True) -> str:
    """Format processable changes for an LLM prompt."""
    formatted_files = []
    for file_path, data in sort_by_priority(filter_processable_files(state_dict)):
        summary = json.dumps(
            data.get("summary"),
            indent=2,
            ensure_ascii=False,
            default=pydantic_encoder,
        )
        metadata = _build_metadata_dict(data) if include_metadata else {}
        formatted_files.append(
            format_file_content(file_path, summary, tag_name=file_path, **metadata)
        )
    return "\n".join(formatted_files)


def format_changes_adaptive(
    state_dict: dict,
    include_metadata: bool = True,
    high_detail_threshold: float = 0.6,
    medium_detail_threshold: float = 0.3,
) -> str:
    """Format changes with detail levels selected by combined relevance."""
    formatted_files = []
    for file_path, data in sort_by_priority(filter_processable_files(state_dict)):
        summary = data.get("summary")
        if not summary:
            continue
        relevance = min(
            data.get("scope_alignment", {}).get("max_relevance", 0.0)
            + (0.3 if data.get("priority", "NORMAL") == "HIGH" else 0.0)
            + min(data.get("term_relevance", {}).get("match_count", 0) / 20.0, 0.2),
            1.0,
        )
        summary_text = json.dumps(
            _prune_summary_by_relevance(
                summary,
                relevance,
                high_detail_threshold,
                medium_detail_threshold,
            ),
            indent=2,
            ensure_ascii=False,
            default=pydantic_encoder,
        )
        metadata = _build_metadata_dict(data) if include_metadata else {}
        if include_metadata:
            metadata["Combined Relevance"] = f"{relevance:.2f}"
        formatted_files.append(
            format_file_content(file_path, summary_text, tag_name=file_path, **metadata)
        )
    return "\n".join(formatted_files)


def _prune_summary_by_relevance(
    summary: dict | str,
    relevance: float,
    high_threshold: float,
    medium_threshold: float,
) -> dict | str:
    """Prune a change summary to a detail level appropriate for relevance."""
    if not isinstance(summary, dict) or relevance >= high_threshold:
        return summary
    if relevance >= medium_threshold:
        pruned = dict(summary)
        if "specific_changes" in pruned:
            pruned["specific_changes"] = [
                {
                    "name": "Details omitted",
                    "summary": f"{len(pruned['specific_changes'])} changes (medium relevance)",
                }
            ]
        return pruned

    pruned = {
        key: summary[key] for key in ("functional_impact", "programming_language") if key in summary
    }
    if "specific_changes" in summary:
        pruned["note"] = (
            f"{len(summary['specific_changes'])} specific changes omitted (low relevance)"
        )
    return pruned
