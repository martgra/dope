from enum import Enum

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
