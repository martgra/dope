from pydantic import BaseModel, Field

from dope.models.enums import (
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)


class DocSectionTemplate(BaseModel):
    """Section of a doc."""

    description: str = Field(
        ..., description="Functional description of the section and expected content."
    )
    themes: list[SectionTheme] = Field(..., description="Theme of the section.")
    roles: list[SectionAudience] | None = Field(
        None, description="Roles which whom the section is relevant for", exclude=True
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
