from pydantic import BaseModel, Field

from dope.models.enums import ChangeType


class DocSection(BaseModel):
    """Summary of a section within the doc."""

    section_name: str = Field(..., description="Name of the section")
    summary: str | None = Field(
        ...,
        description="A detailed description of the section describing current content in the file."
        " Be specific about names, commands or variables in the text. This is intended as a summary"
        "for someone who knows the codebase well.",
    )
    references: list[str] = Field(
        ...,
        description="References to code in the text such as commands,"
        "config values, libraries files etc.",
    )


class DocSummary(BaseModel):
    """Summary of a doc."""

    sections: list[DocSection] | None = Field(
        ...,
        description="List of major headings or sections (e.g., Introduction, Setup, API, Examples)",
    )


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


class CodeMetadata(BaseModel):
    """Repo metadata."""

    commits: int = Field(..., description="number of commits in branch")
    num_contributors: int = Field(..., description="Number of unique contributors.")
    branches: list[str] = Field(..., description="Name of branches in repo.")
    tags: list[str] = Field(..., description="Name of tags in repo.")
    lines_of_code: int = Field(..., description="lines of code in repo")
