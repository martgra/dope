from dope.models.domain.scope import (
    DocSectionTemplate,
    DocTemplate,
    FreshnessLevel,
    UpdateTriggers,
)
from dope.models.enums import DocTemplateKey, ProjectTier, SectionAudience, SectionTheme

TIERS = [ProjectTier.large, ProjectTier.massive]
onboarding_guide = DocTemplate(
    description="Day-one setup instructions and workflows for new team members and contributors.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.user, SectionAudience.management],
    sections={
        "team_overview": DocSectionTemplate(
            description="Introduction to the project mission, team structure, and roles",
            themes=[SectionTheme.introductory, SectionTheme.introductory],
            roles=[SectionAudience.user, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "CONTRIBUTING.md", "docs/**/*.md"],
                change_types={"documentation"},
                min_magnitude=0.3,
                relevant_terms={"team", "overview", "mission", "role", "structure"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "access_and_permissions": DocSectionTemplate(
            description="How to request and configure access to repos, infra, and dashboards",
            themes=[SectionTheme.introductory, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", ".github/**/*"],
                change_types={"configuration", "security"},
                min_magnitude=0.3,
                relevant_terms={"access", "permission", "auth", "security"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "local_dev_setup": DocSectionTemplate(
            description="Steps to clone the repo, install dependencies, and configure a "
            "local dev environment",
            themes=[SectionTheme.technical, SectionTheme.introductory],
            roles=[SectionAudience.user, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "README.md", "Makefile", "requirements*.txt"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"setup", "install", "development", "environment"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "environment_promotion": DocSectionTemplate(
            description="Workflow for promoting changes from dev → staging → production",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "*.yaml", "scripts/**/*"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"promotion", "environment", "deployment", "workflow"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "communication_and_support": DocSectionTemplate(
            description="Key communication channels, mailing lists, "
            "and meeting cadences for questions",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.engineering, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "CONTRIBUTING.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"communication", "support", "contact", "channel"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
    },
)
governance_rfcs = DocTemplate(
    description="Architecture Decision Records (ADRs), RFC process, and deprecation policy.",
    tiers=TIERS,
    roles=[SectionAudience.management],
    sections={
        "adr_index": DocSectionTemplate(
            description="List of all ADRs with summaries and links",
            themes=[SectionTheme.governance, SectionTheme.introductory],
            roles=[SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["docs/**/*.md", "*.md"],
                change_types={"architecture", "documentation"},
                min_magnitude=0.4,
                relevant_terms={"adr", "decision", "architecture", "record"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "rfc_process": DocSectionTemplate(
            description="How to propose, discuss, and approve RFCs or ADRs",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.all],
            update_triggers=UpdateTriggers(
                code_patterns=["CONTRIBUTING.md", "docs/**/*.md"],
                change_types={"documentation"},
                min_magnitude=0.3,
                relevant_terms={"rfc", "process", "proposal", "governance"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "deprecation_policy": DocSectionTemplate(
            description="Criteria and timeline for deprecating features or APIs",
            themes=[SectionTheme.governance, SectionTheme.strategic],
            roles=[SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "CHANGELOG.md"],
                change_types={"api", "feature"},
                min_magnitude=0.4,
                relevant_terms={"deprecation", "policy", "sunset", "removal"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "roadmap_and_milestones": DocSectionTemplate(
            description="High-level timeline of planned features and releases",
            themes=[SectionTheme.strategic],
            roles=[SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "docs/**/*.md"],
                change_types={"feature", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"roadmap", "milestone", "plan", "release"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
    },
)
compliance_manuals = DocTemplate(
    description="Regulatory compliance documentation (GDPR, PCI, HIPAA) and audit processes.",
    tiers=TIERS,
    roles=[SectionAudience.compliance],
    sections={
        "regulatory_scope": DocSectionTemplate(
            description="Which regulations apply (GDPR, PCI, HIPAA) and why",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["docs/**/*.md", "*.yaml"],
                change_types={"security", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"regulatory", "compliance", "gdpr", "regulation"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "compliance_controls": DocSectionTemplate(
            description="Processes and responsibilities for each control area",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml", "docs/**/*.md"],
                change_types={"security", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"compliance", "control", "security", "audit"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "reporting_and_audit": DocSectionTemplate(
            description="Audit-log locations, reporting schedules, and stakeholders",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml"],
                change_types={"security", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"audit", "report", "log", "compliance"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "data_protection": DocSectionTemplate(
            description="Data retention policies, privacy procedures, and breach response",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml"],
                change_types={"security", "configuration"},
                min_magnitude=0.5,
                relevant_terms={"data protection", "privacy", "retention", "breach"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
    },
)

run_cost_capacity_planning = DocTemplate(
    description="Cost modeling, capacity planning, and budgeting workflows.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.finance],
    sections={
        "cost_model_overview": DocSectionTemplate(
            description="Breakdown of cost drivers, billing units, and cost centers",
            themes=[SectionTheme.operational, SectionTheme.strategic],
            roles=[SectionAudience.finance, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml", "Dockerfile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"cost", "billing", "budget", "pricing"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "resource_scaling_forecast": DocSectionTemplate(
            description="Projected resource needs based on historical usage trends",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*.yaml", "*.yml"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"scaling", "forecast", "resource", "capacity"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "budgeting_and_finance_workflow": DocSectionTemplate(
            description="How budgets are proposed, approved, and monitored",
            themes=[SectionTheme.operational, SectionTheme.strategic],
            roles=[SectionAudience.finance, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["docs/**/*.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"budget", "finance", "workflow", "approval"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "optimization_strategies": DocSectionTemplate(
            description="Techniques for cost savings and efficiency improvements",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "*.yaml"],
                change_types={"refactor", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"optimization", "cost", "efficiency", "savings"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
    },
)
glossary = DocTemplate(
    description="Definitions of domain-specific terms, acronyms, and key concepts.",
    tiers=TIERS,
    roles=[SectionAudience.all],
    sections={
        "terms_and_definitions": DocSectionTemplate(
            description="Alphabetical list of domain terms with clear definitions",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.all],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "docs/**/*.md"],
                change_types={"feature", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"term", "definition", "glossary", "terminology"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "acronyms_and_abbreviations": DocSectionTemplate(
            description="Common acronyms and their expanded forms",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.all],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "docs/**/*.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"acronym", "abbreviation", "glossary"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "jargon_and_concepts": DocSectionTemplate(
            description="Explanations of specialized or industry-specific jargon",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.all],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "docs/**/*.md"],
                change_types={"feature", "documentation"},
                min_magnitude=0.2,
                relevant_terms={"jargon", "concept", "terminology", "glossary"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
    },
)
faq_troubleshooting = DocTemplate(
    description="Frequently asked questions and solutions to common issues.",
    tiers=TIERS,
    roles=[SectionAudience.support, SectionAudience.engineering, SectionAudience.user],
    sections={
        "general_faq": DocSectionTemplate(
            description="Answers to frequent high-level questions",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.support],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "docs/**/*.md"],
                change_types={"feature", "bugfix", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"faq", "question", "answer", "help"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "error_handling": DocSectionTemplate(
            description="Common error messages and their usual causes",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "dope/exceptions.py"],
                change_types={"bugfix", "feature"},
                min_magnitude=0.3,
                relevant_terms={"error", "exception", "handling", "troubleshoot"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "logs_and_diagnostics": DocSectionTemplate(
            description="Where to find logs and how to interpret diagnostic data",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"log", "diagnostic", "debug", "troubleshoot"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "escalation_paths": DocSectionTemplate(
            description="When and how to escalate issues to support or engineering",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.support],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "CONTRIBUTING.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"escalation", "support", "contact", "help"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
    },
)

massive = {
    DocTemplateKey.compliance_manuals: compliance_manuals,
    DocTemplateKey.faq_troubleshooting: faq_troubleshooting,
    DocTemplateKey.glossary: glossary,
    DocTemplateKey.governance_rfcs: governance_rfcs,
    DocTemplateKey.onboarding_guide: onboarding_guide,
    DocTemplateKey.run_cost_capacity_planning: run_cost_capacity_planning,
}
