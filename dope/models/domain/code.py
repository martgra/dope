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

    specific_changes: list[CodeChange] = Field(
        None, description="List of detailed changes within the file"
    )
    functional_impact: list[str] = Field(
        ...,
        description="Describe the functional impacts that this particular change will have"
        " on the application.",
    )
    programming_language: str = Field(..., description="Programming language used.")
