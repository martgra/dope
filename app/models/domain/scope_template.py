from enum import Enum

from pydantic import BaseModel, Field


class ProjectTier(str, Enum):
    """Estimated size or complexity of a project."""

    trivial = "trivial"
    small = "small"
    medium = "medium"
    large = "large"
    massive = "massive"


class SectionAudience(str, Enum):
    """Audience for a specific section in the documentation."""

    all = "all"
    management = "management"
    engineering = "engineering"
    user = "user"
    support = "support"
    finance = "finance"
    compliance = "compliance"


class SectionTheme(str, Enum):
    """Content of a secific section."""

    introductory = "introductory"
    technical = "technical"
    operational = "operational"
    governance = "governance"
    strategic = "strategic"


class DocTemplateKey(str, Enum):
    """Doc type in structure."""

    readme = "readme"
    contributing = "contributing"
    quickstart = "quickstart"
    examples_cookbook = "examples_cookbook"
    api_reference = "api_reference"
    changelog = "changelog"
    user_guide = "user_guide"
    tutorials = "tutorials"
    installation_guide = "installation_guide"
    architecture_overview = "architecture_overview"
    developer_guide = "developer_guide"
    testing_guide = "testing_guide"
    ci_cd_release_notes = "ci_cd_release_notes"
    deployment_guide = "deployment_guide"
    operations_runbooks = "operations_runbooks"
    security_compliance = "security_compliance"
    performance_tuning = "performance_tuning"
    monitoring_metrics = "monitoring_metrics"
    onboarding_guide = "onboarding_guide"
    governance_rfcs = "governance_rfcs"
    compliance_manuals = "compliance_manuals"
    run_cost_capacity_planning = "run_cost_capacity_planning"
    glossary = "glossary"
    faq_troubleshooting = "faq_troubleshooting"


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
        """Returns a list of all sections across all documents in the documentation structure.

        Returns:
            List of tuples containing (doc_key, section_name, section_object)
        """
        return self.documentation_structure.keys()


class SuggestedChange(BaseModel):
    """Changes suggested based on reviewing  doc file."""

    filepath: str = Field(..., description="Path to doc file to apply the suggested change to.")
    instructions: str = Field(..., description="Instructions on what has to change in the file.")
    content: str = Field(..., description="Content to add or implement in another file.")


class AlignedScope(BaseModel):
    """Result of aligning scope."""

    content: str = Field(..., description="Markdown content of the modified file.")
    changes_in_other_files: list[SuggestedChange]
