"""Code-related domain models."""

from pydantic import BaseModel, Field


class CodeChange(BaseModel):
    """Change to config files, functions or scripts or other relevant code."""

    name: str = Field(
        ..., description="Name of the variable, library, function or method that was changed"
    )
    summary: str = Field(
        ...,
        description="A detailed explanation of the particular code change",
    )


class CodeChanges(BaseModel):
    """Description of code changes impact on the application."""

    specific_changes: list[CodeChange] | None = Field(
        default=None, description="List of detailed changes within the file"
    )
    functional_impact: list[str] = Field(
        ...,
        description="Describe the functional impacts that this particular change will have"
        " on the application.",
    )
    programming_language: str = Field(..., description="Programming language used.")


class CodeMetadata(BaseModel):
    """Repository metadata for code analysis.

    Attributes:
        commits: Number of commits in the branch
        num_contributors: Number of unique contributors
        branches: List of branch names in the repository
        tags: List of tag names in the repository
        lines_of_code: Total lines of code in the repository
    """

    commits: int = Field(..., description="Number of commits in branch")
    num_contributors: int = Field(..., description="Number of unique contributors")
    branches: list[str] = Field(..., description="Name of branches in repo")
    tags: list[str] = Field(..., description="Name of tags in repo")
    lines_of_code: int = Field(..., description="Lines of code in repo")
