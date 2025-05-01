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
