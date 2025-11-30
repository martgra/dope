"""Enumerations used across dope models."""

from enum import Enum


class Provider(str, Enum):
    """Enum for llm providers."""

    OPENAI = "openai"
    AZURE = "azure"


class ChangeType(str, Enum):
    """Enum to indicate if doc is to be added, modified or deleted."""

    ADD = "add"
    CHANGE = "change_existing"
    DELETE = "delete"


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
    """Content of a specific section."""

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
