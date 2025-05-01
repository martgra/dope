from app.models.domain.scope_template import (
    DocSectionTemplate,
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)

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
        ),
        "access_and_permissions": DocSectionTemplate(
            description="How to request and configure access to repos, infra, and dashboards",
            themes=[SectionTheme.introductory, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.management],
        ),
        "local_dev_setup": DocSectionTemplate(
            description="Steps to clone the repo, install dependencies, and configure a "
            "local dev environment",
            themes=[SectionTheme.technical, SectionTheme.introductory],
            roles=[SectionAudience.user, SectionAudience.engineering],
        ),
        "environment_promotion": DocSectionTemplate(
            description="Workflow for promoting changes from dev → staging → production",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
        ),
        "communication_and_support": DocSectionTemplate(
            description="Key communication channels, mailing lists, "
            "and meeting cadences for questions",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.engineering, SectionAudience.management],
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
        ),
        "rfc_process": DocSectionTemplate(
            description="How to propose, discuss, and approve RFCs or ADRs",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.all],
        ),
        "deprecation_policy": DocSectionTemplate(
            description="Criteria and timeline for deprecating features or APIs",
            themes=[SectionTheme.governance, SectionTheme.strategic],
            roles=[SectionAudience.management],
        ),
        "roadmap_and_milestones": DocSectionTemplate(
            description="High-level timeline of planned features and releases",
            themes=[SectionTheme.strategic],
            roles=[SectionAudience.management],
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
        ),
        "compliance_controls": DocSectionTemplate(
            description="Processes and responsibilities for each control area",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance],
        ),
        "reporting_and_audit": DocSectionTemplate(
            description="Audit-log locations, reporting schedules, and stakeholders",
            themes=[SectionTheme.governance, SectionTheme.operational],
            roles=[SectionAudience.compliance],
        ),
        "data_protection": DocSectionTemplate(
            description="Data retention policies, privacy procedures, and breach response",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.compliance],
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
        ),
        "resource_scaling_forecast": DocSectionTemplate(
            description="Projected resource needs based on historical usage trends",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "budgeting_and_finance_workflow": DocSectionTemplate(
            description="How budgets are proposed, approved, and monitored",
            themes=[SectionTheme.operational, SectionTheme.strategic],
            roles=[SectionAudience.finance, SectionAudience.management],
        ),
        "optimization_strategies": DocSectionTemplate(
            description="Techniques for cost savings and efficiency improvements",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
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
        ),
        "acronyms_and_abbreviations": DocSectionTemplate(
            description="Common acronyms and their expanded forms",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.all],
        ),
        "jargon_and_concepts": DocSectionTemplate(
            description="Explanations of specialized or industry-specific jargon",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.all],
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
        ),
        "error_handling": DocSectionTemplate(
            description="Common error messages and their usual causes",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
        ),
        "logs_and_diagnostics": DocSectionTemplate(
            description="Where to find logs and how to interpret diagnostic data",
            themes=[SectionTheme.operational, SectionTheme.technical],
            roles=[SectionAudience.support, SectionAudience.engineering],
        ),
        "escalation_paths": DocSectionTemplate(
            description="When and how to escalate issues to support or engineering",
            themes=[SectionTheme.operational, SectionTheme.operational],
            roles=[SectionAudience.user, SectionAudience.support],
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
