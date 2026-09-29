"""Tests for the Jev-judgment wiring in change_processor."""

from dope.services.suggester.change_processor import (
    _build_metadata_dict,
    filter_by_judgment_needs_docs,
    sort_by_priority,
)


def _entry(*, judgment=None, priority="NORMAL", magnitude=0.5, summary_extra=None) -> dict:
    """Build a minimal state entry with an optional Jev judgment attached."""
    summary: dict = {"specific_changes": [], "functional_impact": []}
    if judgment is not None:
        summary["judgment"] = judgment
    if summary_extra:
        summary.update(summary_extra)
    return {
        "hash": "abc",
        "summary": summary,
        "priority": priority,
        "metadata": {"magnitude": magnitude},
    }


def test_build_metadata_dict_without_judgment_is_unchanged():
    """Entries lacking a judgment produce metadata that omits the Jev keys."""
    md = _build_metadata_dict(_entry())
    assert "Priority" in md
    assert "Change Magnitude" in md
    assert "Breaking Change" not in md
    assert "Doc Priority" not in md


def test_build_metadata_dict_surfaces_judgment_fields():
    """A full judgment lifts every field into first-class metadata keys."""
    judgment = {
        "change_category": "feature",
        "change_type": "add",
        "is_breaking": False,
        "is_user_facing": True,
        "needs_docs": True,
        "doc_priority": 3,
    }
    md = _build_metadata_dict(_entry(judgment=judgment))
    assert md["Jev Category"] == "feature"
    assert md["Jev Change Type"] == "add"
    assert md["Breaking Change"] == "no"
    assert md["User-Facing"] == "yes"
    assert md["Needs Docs"] == "yes"
    assert md["Doc Priority"] == "3/4"


def test_filter_by_judgment_drops_only_explicit_no():
    """needs_docs=false drops; missing judgment or =true keeps the entry."""
    state = {
        "a.py": _entry(judgment={"needs_docs": True}),
        "b.py": _entry(judgment={"needs_docs": False}),
        "c.py": _entry(judgment=None),  # unknown → keep
        "d.py": _entry(judgment={"is_breaking": True}),  # no needs_docs key → keep
    }
    kept = filter_by_judgment_needs_docs(state)
    assert set(kept.keys()) == {"a.py", "c.py", "d.py"}


def test_sort_by_priority_prefers_high_priority_then_jev_priority_then_magnitude():
    """HIGH-priority wins, then Jev doc_priority desc, then magnitude desc."""
    state = {
        "normal_low_jev": _entry(
            priority="NORMAL", judgment={"doc_priority": 1}, magnitude=0.9
        ),
        "high_low_jev": _entry(
            priority="HIGH", judgment={"doc_priority": 0}, magnitude=0.1
        ),
        "normal_high_jev": _entry(
            priority="NORMAL", judgment={"doc_priority": 4}, magnitude=0.5
        ),
        "normal_no_jev_high_mag": _entry(priority="NORMAL", magnitude=0.95),
    }
    order = [path for path, _ in sort_by_priority(state)]
    # HIGH always first
    assert order[0] == "high_low_jev"
    # Among NORMAL, Jev priority 4 beats the rest
    assert order[1] == "normal_high_jev"
    # Then Jev priority 1 beats the no-Jev fallback (-1)
    assert order[2] == "normal_low_jev"
    # Fallback last
    assert order[3] == "normal_no_jev_high_mag"


def test_sort_by_priority_no_judgment_matches_old_behavior():
    """With no judgments anywhere, sort collapses to HIGH first then magnitude desc."""
    state = {
        "a": _entry(priority="NORMAL", magnitude=0.3),
        "b": _entry(priority="HIGH", magnitude=0.1),
        "c": _entry(priority="NORMAL", magnitude=0.8),
    }
    order = [path for path, _ in sort_by_priority(state)]
    assert order == ["b", "c", "a"]
