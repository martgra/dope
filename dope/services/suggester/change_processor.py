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


def _judgment(data: dict) -> dict | None:
    """Return the Jev DiffJudgment on a state entry, if the describer attached one."""
    summary = data.get("summary") or {}
    if not isinstance(summary, dict):
        return None
    judgment = summary.get("judgment")
    return judgment if isinstance(judgment, dict) else None


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
    if scope_alignment:
        if scope_alignment.get("max_relevance", 0.0) > 0:
            result["Scope Relevance"] = f"{scope_alignment['max_relevance']:.2f}"
        if category := scope_alignment.get("category"):
            result["Category"] = category
        if sections := scope_alignment.get("relevant_sections", []):
            result["Affects Docs"] = ", ".join(
                f"{section['doc']}.{section['section']}" for section in sections[:3]
            )

    # Surface Jev's typed judgments as first-class metadata so the suggester
    # prompt can name them directly. Absent when the describer wasn't wired
    # to judge_diff (TypeSafe not configured), so keys only appear if the
    # signal is available — the SUGGESTION_PROMPT v2-judgment references
    # these exact key names.
    judgment = _judgment(data)
    if judgment is not None:
        if "change_category" in judgment:
            result["Jev Category"] = str(judgment["change_category"])
        if "change_type" in judgment:
            result["Jev Change Type"] = str(judgment["change_type"])
        if "is_breaking" in judgment:
            result["Breaking Change"] = "yes" if judgment["is_breaking"] else "no"
        if "is_user_facing" in judgment:
            result["User-Facing"] = "yes" if judgment["is_user_facing"] else "no"
        if "needs_docs" in judgment:
            result["Needs Docs"] = "yes" if judgment["needs_docs"] else "no"
        if "doc_priority" in judgment:
            result["Doc Priority"] = f"{judgment['doc_priority']}/4"
    return result


def filter_processable_files(state_dict: dict) -> dict:
    """Return non-skipped files that have summaries."""
    return {
        file_path: data
        for file_path, data in state_dict.items()
        if not data.get("skipped") and data.get("summary")
    }


def filter_by_judgment_needs_docs(state_dict: dict) -> dict:
    """Drop files whose Jev DiffJudgment says ``needs_docs`` is false.

    A missing judgment (TypeSafe not configured, or older state entries)
    is treated as "unknown" and kept — this filter never drops files
    without an explicit ``needs_docs=False`` signal. Enable via
    :class:`ScopeFilterSettings.enable_judgment_gate`.
    """
    kept: dict = {}
    for file_path, data in state_dict.items():
        judgment = _judgment(data)
        if judgment is not None and judgment.get("needs_docs") is False:
            continue
        kept[file_path] = data
    return kept


def _sort_key(item: tuple[str, dict]) -> tuple[int, int, float]:
    """Ranking tuple: HIGH-priority > Jev doc_priority desc > magnitude desc."""
    _file_path, data = item
    priority_rank = 0 if data.get("priority", "NORMAL") == "HIGH" else 1
    judgment = _judgment(data)
    jev_priority = judgment.get("doc_priority", -1) if judgment else -1
    magnitude = data.get("metadata", {}).get("magnitude", 0.0)
    return (priority_rank, -jev_priority, -magnitude)


def sort_by_priority(state_dict: dict) -> list[tuple[str, dict]]:
    """Sort files by HIGH priority, then Jev doc_priority, then magnitude."""
    return sorted(state_dict.items(), key=_sort_key)


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
