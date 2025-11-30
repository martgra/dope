from dope.models.domain.scope_template import (
    DocSectionTemplate,
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)

TIERS = [ProjectTier.medium, ProjectTier.large, ProjectTier.massive]


user_guide = DocTemplate(
    description="Task-oriented manual guiding end users through core workflows.",
    tiers=TIERS,
    roles=[SectionAudience.user],
    sections={
        "introduction_and_concepts": DocSectionTemplate(
            description="Overview of key concepts and terminology for end users",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.user],
        ),
        "core_workflows": DocSectionTemplate(
            description="Step-by-step instructions for the most common tasks",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "advanced_usage": DocSectionTemplate(
            description="Guidance on power-user features and edge-case scenarios",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "accessibility_and_localization": DocSectionTemplate(
            description="Notes on accessibility features and supported locales",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "faqs_and_common_pitfalls": DocSectionTemplate(
            description="Answers to frequent questions and workarounds for known issues",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.user],
        ),
    },
)

tutorials = DocTemplate(
    description="Step-by-step walkthroughs for learning features and end-to-end scenarios.",
    tiers=TIERS,
    roles=[SectionAudience.user],
    sections={
        "series_overview": DocSectionTemplate(
            description="High-level description of the tutorial series and learning goals",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.user],
        ),
        "tutorial_1_getting_started": DocSectionTemplate(
            description="Walks new users through their first end-to-end scenario",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "tutorial_2_intermediate_workflow": DocSectionTemplate(
            description="Shows how to combine multiple features in a practical workflow",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "tutorial_3_advanced_scenario": DocSectionTemplate(
            description="Demonstrates an advanced use case or integration",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
        "extending_and_customizing": DocSectionTemplate(
            description="How to adapt the tutorials for custom environments or needs",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
        ),
    },
)

installation_guide = DocTemplate(
    description="Detailed installation instructions including prerequisites and configuration.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "supported_platforms": DocSectionTemplate(
            description="Operating systems, runtimes, and hardware requirements",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "system_requirements": DocSectionTemplate(
            description="Versions of dependencies (DBs, runtimes, libraries)",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "environment_setup": DocSectionTemplate(
            description="Environment variables, virtual environments, container setup",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "installation_methods": DocSectionTemplate(
            description="Package manager, container/image, or source-build options",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "post_install_validation": DocSectionTemplate(
            description="Commands or checks to confirm a successful install",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "uninstall_and_cleanup": DocSectionTemplate(
            description="Steps to fully remove the software and its artifacts",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
    },
)

architecture_overview = DocTemplate(
    description="Diagrams and explanations of system architecture and component interactions.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "system_context": DocSectionTemplate(
            description="High-level diagram showing actors, systems, and boundaries",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering],
        ),
        "component_diagram": DocSectionTemplate(
            description="Breakdown of major modules/services and their interactions",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering],
        ),
        "data_flow": DocSectionTemplate(
            description="Visualization of how data moves through the system",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering],
        ),
        "deployment_topology": DocSectionTemplate(
            description="Mapping of components to environments, regions, and nodes",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "technology_stack": DocSectionTemplate(
            description="List of frameworks, languages, and infrastructure choices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
    },
)

developer_guide = DocTemplate(
    description="Coding conventions, branching strategy, and developer best practices.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "repo_and_module_structure": DocSectionTemplate(
            description="Directory layout and responsibilities of each module",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "branching_and_git_workflow": DocSectionTemplate(
            description="Branch naming, pull-request etiquette, and merge strategy",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
        ),
        "coding_standards": DocSectionTemplate(
            description="Style guide rules, linting, and formatting conventions",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "dependency_management": DocSectionTemplate(
            description="How to add, update, and lock external dependencies",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "debugging_and_logging": DocSectionTemplate(
            description="Techniques for breakpoints, logging levels, and tracing",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
    },
)

testing_guide = DocTemplate(
    description="Instructions for writing and running tests, and interpreting coverage metrics.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "test_categories": DocSectionTemplate(
            description="Overview of unit, integration, end-to-end, and performance tests",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "running_tests_locally": DocSectionTemplate(
            description="Commands and setup for executing tests on a dev machine",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "ci_test_workflow": DocSectionTemplate(
            description="How tests are run in CI, gating rules, and failure handling",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "writing_new_tests": DocSectionTemplate(
            description="Guidelines and examples for authoring effective test cases",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "coverage_and_metrics": DocSectionTemplate(
            description="How to measure code coverage and interpret quality reports",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
    },
)

ci_cd_release_notes = DocTemplate(
    description="Overview of CI/CD pipeline stages, artifact management, and release workflow.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "pipeline_overview": DocSectionTemplate(
            description="Diagram or description of CI/CD stages from commit to deploy",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "stage_definitions": DocSectionTemplate(
            description="Details on build, test, package, and deployment steps",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "artifact_management": DocSectionTemplate(
            description="How build artifacts are versioned, stored, and retrieved",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "release_versioning": DocSectionTemplate(
            description="Semantic versioning rules and tagging strategy",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
        ),
        "rollback_strategy": DocSectionTemplate(
            description="Procedures for reverting a faulty deployment",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "changelog_format": DocSectionTemplate(
            description="Template and conventions for documenting release notes",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
        ),
    },
)


medium = {
    DocTemplateKey.architecture_overview: architecture_overview,
    DocTemplateKey.ci_cd_release_notes: ci_cd_release_notes,
    DocTemplateKey.deployment_guide: developer_guide,
    DocTemplateKey.installation_guide: installation_guide,
    DocTemplateKey.testing_guide: testing_guide,
    DocTemplateKey.tutorials: tutorials,
    DocTemplateKey.user_guide: user_guide,
}
