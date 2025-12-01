"""Documentation-related domain models."""

from pydantic import BaseModel, Field

from dope.models.enums import ChangeType


class DocSection(BaseModel):
    """Summary of a section within a documentation file.

    Attributes:
        section_name: Name of the section/heading
        summary: Detailed description of the section content
        references: Code references mentioned in the section
    """

    section_name: str = Field(..., description="Name of the section")
    summary: str | None = Field(
        ...,
        description=(
            "A detailed description of the section describing current content in the file. "
            "Be specific about names, commands or variables in the text. This is intended as a "
            "summary for someone who knows the codebase well."
        ),
    )
    references: list[str] = Field(
        ...,
        description=(
            "References to code in the text such as commands, config values, libraries, files etc."
        ),
    )


class DocSummary(BaseModel):
    """Summary of a documentation file.

    Attributes:
        sections: List of major sections in the document
    """

    sections: list[DocSection] | None = Field(
        ...,
        description="List of major headings or sections (e.g., Introduction, Setup, API, Examples)",
    )


class ChangeSuggestion(BaseModel):
    """A specific change suggestion for a documentation section.

    Attributes:
        suggestion: Detailed instructions for the change
        code_references: Related code files for context
    """

    suggestion: str = Field(
        ...,
        description=(
            "List of detailed and specific instructions to what changes to apply to the "
            "documentation file based on the code changes. "
            "All changes related to this file are grouped here."
        ),
    )
    code_references: list[str] = Field(
        ...,
        description="Files with code changes that are important to apply this change.",
    )


class SuggestedChange(BaseModel):
    """All changes to apply to a specific documentation file.

    Attributes:
        change_type: Type of change (add, modify, or delete)
        documentation_file_path: Path to the target documentation file
        suggested_changes: List of specific changes to apply
    """

    change_type: ChangeType = Field(
        ...,
        description=(
            "Indicate if this change is to add a new file, change an existing file, "
            "or delete a redundant file."
        ),
        json_schema_extra={"example": ChangeType.ADD},
    )
    documentation_file_path: str = Field(
        ...,
        description="Path to the documentation file to add, change, or delete.",
        json_schema_extra={"example": "docs/readme.md"},
    )
    suggested_changes: list[ChangeSuggestion] = Field(
        ...,
        description="List of particular changes.",
    )


class DocSuggestions(BaseModel):
    """Collection of documentation changes based on code changes.

    Attributes:
        changes_to_apply: List of changes, one per documentation file
    """

    changes_to_apply: list[SuggestedChange] = Field(
        ...,
        description=(
            "List of changes to apply to documentation, keyed by the unique documentation file "
            "path. This ensures that each file path occurs only once."
        ),
    )
