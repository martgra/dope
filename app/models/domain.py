from enum import Enum

from pydantic import BaseModel, Field


class CodeChangeType(str, Enum):
    """Enum that indicates if the change was a add, modify or remove."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class CodeChange(BaseModel):
    """Change to config files, functions or scripts or other relevant code."""

    name: str = Field(
        ..., description="Name of the variable, library, function or method that was changed"
    )
    summary: str = Field(..., description="A codehuman readable explanation of the change.")
    change_type: CodeChangeType = Field(
        ..., description="Was this change a delete, modification or add?."
    )


class CodeChanges(BaseModel):
    """Description of code changes impact on the application."""

    specific_changes: list[CodeChange] | None = Field(
        None, description="Optional list of detailed changes within the file"
    )
    diff_summary: str | None = Field(
        None,
        description="A detailed human-readable summary of the diff."
        "The summary must be enough to identify potential documentation that needs updating.",
    )
    functional_impact: list[str] = Field(
        ...,
        description="Functional impacts that this particular change will have on the application.",
    )
    programming_language: str = Field(..., description="Programming language used.")


class DocSection(BaseModel):
    """Summary of a section within the doc."""

    section_name: str = Field(..., description="Name of the section")
    summary: str | None = Field(
        ...,
        description="A Summary of the section describing current content. Not to fill if the "
        "section is empty.",
    )
    code_references: list[str] | None = Field(
        None,
        description="List of specific code modules, functions, classes, or APIs mentioned in the "
        "section.",
    )
    configuration_details: list[str] | None = Field(
        None,
        description="Instructions or parameters related to configuration, setup, or dependencies in"
        " the section.",
    )
    usage_examples: list[str] | None = Field(
        None, description="Any usage examples, commands, or code snippets in the section."
    )

    dependencies: list[str] | None = Field(
        None, description="Libraries, frameworks, or services referenced in the section."
    )


class DocSummary(BaseModel):
    """Summary of a doc."""

    purpose: str | None = Field(
        ..., description="A brief description of what the document is intended to cover"
    )
    scope: str | None = Field(
        None, description="The main topics and functionalities the document addresses"
    )
    sections: list[DocSection] | None = Field(
        ...,
        description="List of major headings or sections (e.g., Introduction, Setup, API, Examples)",
    )


class ChangeType(str, Enum):
    """Enum to indicate if doc is to be added, modified or deleted."""

    ADD = "add"
    CHANGE = "change_existing"
    DELETE = "delete"


class ChangeSuggestion(BaseModel):
    """Change suggestion for a specific doc part based on code."""

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
    """All changes to apply to a particular documentation file."""

    change_type: ChangeType = Field(
        ...,
        description="Indicate if this change is to add a new file, change an existing file, "
        "or delete a redundant file.",
        example=ChangeType.ADD,
    )
    documentation_file_path: str = Field(
        ...,
        description="Path to the documentation file to add, change, or delete.",
        example="docs/readme.md",
    )
    suggested_changes: list[ChangeSuggestion] = Field(
        ..., description="List of particular changes."
    )


class DocSuggestions(BaseModel):
    """Changes to apply to the whole documentation based on code changes."""

    changes_to_apply: list[SuggestedChange] = Field(
        ...,
        description=(
            "List of changes to apply to documentation, keyed by the unique documentation file "
            "path. This ensures that each file path occurs only once."
        ),
    )
