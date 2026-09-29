"""Domain models for scope templates, alignment results, and line-level edits."""
# ruff: noqa: UP042

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from dope.models.enums import (
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)


class FreshnessLevel(str, Enum):
    """Freshness requirement for documentation sections.

    Indicates how frequently a section should be updated relative to code changes.
    """

    CRITICAL = "critical"  # Must be updated immediately (e.g., breaking changes)
    HIGH = "high"  # Should be updated within release cycle
    MEDIUM = "medium"  # Can wait for minor versions
    LOW = "low"  # Rarely needs updates


class UpdateTriggers(BaseModel):
    """Defines what code changes should trigger documentation updates.

    Attributes:
        code_patterns: Glob patterns for file paths that affect this section
        change_types: Set of change categories that are relevant
        min_magnitude: Minimum change magnitude (0-1) to trigger update
        relevant_terms: Keywords indicating relevance to this section

    Example:
        >>> triggers = UpdateTriggers(
        ...     code_patterns=["dope/cli/*.py", "README.md"],
        ...     change_types={"cli", "configuration"},
        ...     min_magnitude=0.3,
        ...     relevant_terms={"command", "argument", "option"}
        ... )
    """

    code_patterns: list[str] = Field(default_factory=list)
    change_types: set[str] = Field(default_factory=set)
    min_magnitude: float = Field(default=0.3)
    relevant_terms: set[str] = Field(default_factory=set)


class DocSectionTemplate(BaseModel):
    """Section of a doc."""

    description: str = Field(
        ..., description="Functional description of the section and expected content."
    )
    themes: list[SectionTheme] = Field(..., description="Theme of the section.")
    roles: list[SectionAudience] | None = Field(
        None, description="Roles which whom the section is relevant for", exclude=True
    )
    update_triggers: UpdateTriggers = Field(
        default_factory=UpdateTriggers,
        description="What code changes should trigger updates to this section",
    )
    freshness_requirement: FreshnessLevel = Field(
        default=FreshnessLevel.MEDIUM, description="How frequently this section needs updates"
    )


class DocTemplate(BaseModel):
    """Template for a doc in a doc structure."""

    tiers: list[ProjectTier] | None = Field(
        None, description="Tier the doc is suited for.", exclude=True
    )
    roles: list[SectionAudience] | None = Field(
        None, description="Roles for whom the document is relevant", exclude=True
    )
    implemented_in_path: str | None = Field(
        None, description="Path to the implementation of the documentation."
    )
    description: str = Field(
        ..., description="Functional description of the documentation and expected content."
    )
    sections: dict[str, DocSectionTemplate] = Field(..., description="Sections in the doc.")


class StructureTemplate(BaseModel):
    """Template for a doc structure."""

    docs: dict[DocTemplateKey, DocTemplate]


class ScopeTemplate(BaseModel):
    """Scope Template."""

    size: ProjectTier = Field(..., description="The perceived complexity tier of the application")
    documentation_structure: dict[DocTemplateKey, DocTemplate] = Field(
        ..., description="The set of documentation sections to include"
    )

    def get_all_documents(self) -> set[DocTemplateKey]:
        """Returns a set of all document keys in the documentation structure.

        Returns:
            Set of document template keys
        """
        # pylint: disable=no-member  # Pylint confused by Pydantic Field descriptor
        return set(self.documentation_structure.keys())


class SuggestedChange(BaseModel):
    """Changes suggested based on reviewing  doc file."""

    filepath: str = Field(..., description="Path to doc file to apply the suggested change to.")
    instructions: str = Field(..., description="Instructions on what has to change in the file.")
    content: str = Field(..., description="Content to add or implement in another file.")


class AlignedScope(BaseModel):
    """Result of aligning scope."""

    content: str = Field(..., description="Markdown content of the modified file.")
    changes_in_other_files: list[SuggestedChange]


class LineEdit(BaseModel):
    """A single line-level edit against a numbered source file.

    Line indices are 1-based (matching the numbering fed to the model)
    and refer to the ORIGINAL source. All edits in a batch address the
    original line numbers; ``apply_edits`` handles index shifts by
    applying edits in reverse order.
    """

    mode: Literal["insert_after", "replace_range", "delete_range"] = Field(
        ...,
        description=(
            "How this edit modifies the source: `insert_after` puts `content` "
            "as new line(s) after `line_start`; `replace_range` swaps lines "
            "`line_start..line_end` with `content`; `delete_range` removes "
            "lines `line_start..line_end` and ignores `content`."
        ),
    )
    line_start: int = Field(
        ...,
        ge=0,
        description=(
            "1-based line number in the ORIGINAL file. For `insert_after`, "
            "`0` means insert at the very top of the file."
        ),
    )
    line_end: int | None = Field(
        default=None,
        description=(
            "Inclusive end line for `replace_range` and `delete_range`. Ignored for `insert_after`."
        ),
    )
    content: str = Field(
        default="",
        description=(
            "New text for `insert_after` and `replace_range`. Should include "
            "any needed trailing newline. Ignored for `delete_range`."
        ),
    )


class EditedScope(BaseModel):
    """Diff-based alternative to :class:`AlignedScope`.

    Instead of the model reproducing the whole doc, it returns only the
    edits it wants to apply. A caller reconstructs the final content via
    :func:`apply_edits`. This structurally prevents the over-rewriting
    failure mode: content the model does not touch stays byte-identical.
    """

    edits: list[LineEdit] = Field(
        default_factory=list,
        description=(
            "Line-level edits to apply, in ANY order. If empty the file "
            "is already aligned and should be left untouched."
        ),
    )
    changes_in_other_files: list[SuggestedChange] = Field(
        default_factory=list,
        description="Same semantics as on AlignedScope.",
    )


class NarrowLineEdit(BaseModel):
    """A line-level edit restricted to insert-or-delete.

    The v3-diff aligner's failure mode was ``replace_range`` abuse: the
    model swapped fine lines for slightly-different versions of
    themselves, defeating the ``EditedScope`` architecture's whole
    point. This narrower type removes ``replace_range`` from the mode
    Literal — any structural rewrite must decompose into an explicit
    delete followed by an insert, which the eval catches as separate
    edits with obvious char-delta cost.
    """

    mode: Literal["insert_after", "delete_range"] = Field(
        ...,
        description=(
            "How this edit modifies the source: `insert_after` puts `content` "
            "as new line(s) after `line_start` (0 = prepend); `delete_range` "
            "removes lines `line_start..line_end` inclusive and ignores `content`."
        ),
    )
    line_start: int = Field(
        ...,
        ge=0,
        description=(
            "1-based line number in the ORIGINAL file. For `insert_after`, "
            "`0` means insert at the very top of the file."
        ),
    )
    line_end: int | None = Field(
        default=None,
        description="Inclusive end line for `delete_range`. Ignored for `insert_after`.",
    )
    content: str = Field(
        default="",
        description=(
            "New text for `insert_after`. Should include any needed trailing "
            "newline. Ignored for `delete_range`."
        ),
    )


class NarrowEditedScope(BaseModel):
    """Diff output for the narrow aligner (v4-diff).

    Same shape as :class:`EditedScope` but its edit type is
    :class:`NarrowLineEdit`, which forbids ``replace_range`` at the
    schema level.
    """

    edits: list[NarrowLineEdit] = Field(
        default_factory=list,
        description=(
            "Line-level edits to apply, in ANY order. If empty the file "
            "is already aligned and should be left untouched."
        ),
    )
    changes_in_other_files: list[SuggestedChange] = Field(
        default_factory=list,
        description="Same semantics as on AlignedScope.",
    )


def apply_edits(source: str, edits: list[LineEdit] | list[NarrowLineEdit]) -> str:
    """Return ``source`` with all ``edits`` applied.

    Accepts either :class:`LineEdit` (three modes) or
    :class:`NarrowLineEdit` (two modes) since both share the same
    ``mode`` / ``line_start`` / ``line_end`` / ``content`` shape.

    Edits are applied in reverse ``line_start`` order so earlier edits
    do not need to know about index shifts caused by later ones. Line
    indices are treated as 1-based; ``line_start=0`` on an
    ``insert_after`` means "prepend to the file". Trailing newlines on
    ``content`` are preserved as given.

    Args:
        source: Original file text.
        edits: The edits to apply.

    Returns:
        The reconstructed file content.
    """
    lines: list[str] = source.splitlines(keepends=True)
    for edit in sorted(edits, key=lambda e: e.line_start, reverse=True):
        _apply_one(lines, edit)
    return "".join(lines)


def _apply_one(lines: list[str], edit: LineEdit | NarrowLineEdit) -> None:
    """In-place application of a single edit to a mutable line buffer."""
    content_lines = edit.content.splitlines(keepends=True) if edit.content else []
    if edit.mode == "insert_after":
        insertion_idx = edit.line_start  # 0-based index of the first NEW line
        lines[insertion_idx:insertion_idx] = content_lines
        return
    end = edit.line_end if edit.line_end is not None else edit.line_start
    start_idx = edit.line_start - 1  # inclusive, 0-based
    stop_idx = end  # exclusive, 0-based
    if edit.mode == "replace_range":
        lines[start_idx:stop_idx] = content_lines
    elif edit.mode == "delete_range":
        del lines[start_idx:stop_idx]
