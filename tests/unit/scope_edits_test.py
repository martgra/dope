"""Unit tests for LineEdit, EditedScope, and apply_edits."""

from dope.models.domain.scope import LineEdit, apply_edits


def test_apply_edits_no_edits_is_identity():
    """No edits leaves the source byte-identical."""
    source = "line 1\nline 2\nline 3\n"
    assert apply_edits(source, []) == source


def test_apply_edits_insert_after_appends():
    """insert_after with line_start at last line puts content at the end."""
    source = "a\nb\n"
    edits = [LineEdit(mode="insert_after", line_start=2, content="c\n")]
    assert apply_edits(source, edits) == "a\nb\nc\n"


def test_apply_edits_insert_after_zero_prepends():
    """insert_after with line_start=0 prepends to the file."""
    source = "a\nb\n"
    edits = [LineEdit(mode="insert_after", line_start=0, content="header\n")]
    assert apply_edits(source, edits) == "header\na\nb\n"


def test_apply_edits_insert_after_middle_places_before_next_line():
    """insert_after between two lines slots content there."""
    source = "a\nb\nc\n"
    edits = [LineEdit(mode="insert_after", line_start=1, content="x\n")]
    assert apply_edits(source, edits) == "a\nx\nb\nc\n"


def test_apply_edits_replace_range_swaps_inclusive_slice():
    """replace_range replaces the inclusive line_start..line_end slice."""
    source = "a\nb\nc\nd\n"
    edits = [LineEdit(mode="replace_range", line_start=2, line_end=3, content="X\nY\n")]
    assert apply_edits(source, edits) == "a\nX\nY\nd\n"


def test_apply_edits_delete_range_removes_inclusive_slice():
    """delete_range removes the inclusive line_start..line_end slice."""
    source = "a\nb\nc\nd\n"
    edits = [LineEdit(mode="delete_range", line_start=2, line_end=3)]
    assert apply_edits(source, edits) == "a\nd\n"


def test_apply_edits_multiple_edits_addressed_by_original_line_numbers():
    """All edits refer to ORIGINAL line numbers; apply_edits handles shifts."""
    source = "a\nb\nc\nd\ne\n"
    edits = [
        LineEdit(mode="delete_range", line_start=2, line_end=2),  # remove "b"
        LineEdit(mode="insert_after", line_start=4, content="X\n"),  # after "d"
    ]
    # Even though deleting "b" would normally shift subsequent indices, both
    # edits reference the ORIGINAL numbering and apply_edits processes them
    # right-to-left so the second edit still resolves against the original.
    assert apply_edits(source, edits) == "a\nc\nd\nX\ne\n"


def test_apply_edits_replace_range_without_end_treats_as_single_line():
    """replace_range with line_end=None replaces just line_start."""
    source = "a\nb\nc\n"
    edits = [LineEdit(mode="replace_range", line_start=2, content="B\n")]
    assert apply_edits(source, edits) == "a\nB\nc\n"


def test_apply_edits_source_without_trailing_newline_preserved():
    """Sources missing a trailing newline are preserved when untouched."""
    source = "a\nb"
    edits = [LineEdit(mode="insert_after", line_start=1, content="mid\n")]
    assert apply_edits(source, edits) == "a\nmid\nb"
