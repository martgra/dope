from dope.models.domain.scope import (
    DocSectionTemplate,
    DocTemplate,
    FreshnessLevel,
    UpdateTriggers,
)
from dope.models.enums import DocTemplateKey, ProjectTier, SectionAudience, SectionTheme

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
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "docs/**/*.md", "dope/core/*.py"],
                change_types={"feature", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"concept", "terminology", "overview", "introduction"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "core_workflows": DocSectionTemplate(
            description="Step-by-step instructions for the most common tasks",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/cli/*.py", "dope/services/*.py", "examples/*.py"],
                change_types={"feature", "api", "cli"},
                min_magnitude=0.4,
                relevant_terms={"workflow", "task", "command", "usage"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "advanced_usage": DocSectionTemplate(
            description="Guidance on power-user features and edge-case scenarios",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "dope/llms/*.py"],
                change_types={"feature", "api"},
                min_magnitude=0.3,
                relevant_terms={"advanced", "power-user", "edge-case", "complex"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "accessibility_and_localization": DocSectionTemplate(
            description="Notes on accessibility features and supported locales",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/cli/*.py", "resources/**/*"],
                change_types={"feature", "configuration"},
                min_magnitude=0.2,
                relevant_terms={"accessibility", "localization", "locale", "i18n"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "faqs_and_common_pitfalls": DocSectionTemplate(
            description="Answers to frequent questions and workarounds for known issues",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "tests/**/*.py"],
                change_types={"bugfix", "feature"},
                min_magnitude=0.3,
                relevant_terms={"faq", "pitfall", "issue", "workaround", "problem"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
            update_triggers=UpdateTriggers(
                code_patterns=["docs/**/*.md", "examples/**/*"],
                change_types={"feature", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"tutorial", "learning", "overview", "series"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "tutorial_1_getting_started": DocSectionTemplate(
            description="Walks new users through their first end-to-end scenario",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/cli/*.py", "examples/*.py", "README.md"],
                change_types={"feature", "cli"},
                min_magnitude=0.4,
                relevant_terms={"getting started", "tutorial", "first", "beginner"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "tutorial_2_intermediate_workflow": DocSectionTemplate(
            description="Shows how to combine multiple features in a practical workflow",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "examples/*.py"],
                change_types={"feature", "api"},
                min_magnitude=0.4,
                relevant_terms={"workflow", "intermediate", "tutorial", "combine"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "tutorial_3_advanced_scenario": DocSectionTemplate(
            description="Demonstrates an advanced use case or integration",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/llms/*.py", "dope/services/**/*.py"],
                change_types={"feature", "api"},
                min_magnitude=0.3,
                relevant_terms={"advanced", "integration", "tutorial", "use case"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "extending_and_customizing": DocSectionTemplate(
            description="How to adapt the tutorials for custom environments or needs",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/services/**/*.py", "dope/core/*.py"],
                change_types={"feature", "api", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"extend", "customize", "adapt", "configuration"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "README.md", ".github/**/*.yml"],
                change_types={"configuration"},
                min_magnitude=0.3,
                relevant_terms={"platform", "os", "runtime", "requirement"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "system_requirements": DocSectionTemplate(
            description="Versions of dependencies (DBs, runtimes, libraries)",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "requirements*.txt"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"dependency", "version", "requirement", "library"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "environment_setup": DocSectionTemplate(
            description="Environment variables, virtual environments, container setup",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["Dockerfile", ".env*", "pyproject.toml", "Makefile"],
                change_types={"configuration", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"environment", "variable", "setup", "container"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "installation_methods": DocSectionTemplate(
            description="Package manager, container/image, or source-build options",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "setup.py", "Makefile", "Dockerfile"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"install", "package", "build", "deployment"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "post_install_validation": DocSectionTemplate(
            description="Commands or checks to confirm a successful install",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/cli/*.py", "tests/**/*.py"],
                change_types={"cli", "testing"},
                min_magnitude=0.3,
                relevant_terms={"validation", "verify", "test", "check"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "uninstall_and_cleanup": DocSectionTemplate(
            description="Steps to fully remove the software and its artifacts",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "Makefile"],
                change_types={"configuration"},
                min_magnitude=0.2,
                relevant_terms={"uninstall", "cleanup", "remove"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
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
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py", "README.md"],
                change_types={"architecture", "feature"},
                min_magnitude=0.4,
                relevant_terms={"architecture", "system", "context", "boundary"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "component_diagram": DocSectionTemplate(
            description="Breakdown of major modules/services and their interactions",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/__init__.py", "dope/services/**/*.py", "dope/core/*.py"],
                change_types={"architecture", "refactor"},
                min_magnitude=0.4,
                relevant_terms={"component", "module", "service", "interaction"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "data_flow": DocSectionTemplate(
            description="Visualization of how data moves through the system",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/models/**/*.py", "dope/services/**/*.py"],
                change_types={"architecture", "api"},
                min_magnitude=0.4,
                relevant_terms={"data flow", "pipeline", "data", "processing"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "deployment_topology": DocSectionTemplate(
            description="Mapping of components to environments, regions, and nodes",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["Dockerfile", "*.yaml", "*.yml", ".github/**/*"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"deployment", "topology", "environment", "infrastructure"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "technology_stack": DocSectionTemplate(
            description="List of frameworks, languages, and infrastructure choices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "requirements*.txt", "Dockerfile"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"technology", "stack", "framework", "infrastructure"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
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
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/__init__.py", "dope/**/"],
                change_types={"architecture", "refactor"},
                min_magnitude=0.4,
                relevant_terms={"structure", "module", "directory", "organization"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "branching_and_git_workflow": DocSectionTemplate(
            description="Branch naming, pull-request etiquette, and merge strategy",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "CONTRIBUTING.md"],
                change_types={"configuration"},
                min_magnitude=0.3,
                relevant_terms={"git", "branch", "workflow", "pull request"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "coding_standards": DocSectionTemplate(
            description="Style guide rules, linting, and formatting conventions",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", ".pre-commit-config.yaml", "*.cfg"],
                change_types={"configuration"},
                min_magnitude=0.3,
                relevant_terms={"style", "lint", "format", "standard"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "dependency_management": DocSectionTemplate(
            description="How to add, update, and lock external dependencies",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "requirements*.txt", "uv.lock"],
                change_types={"configuration"},
                min_magnitude=0.4,
                relevant_terms={"dependency", "package", "version", "lock"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "debugging_and_logging": DocSectionTemplate(
            description="Techniques for breakpoints, logging levels, and tracing",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["dope/**/*.py"],
                change_types={"feature", "refactor"},
                min_magnitude=0.3,
                relevant_terms={"debug", "log", "trace", "error"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
            update_triggers=UpdateTriggers(
                code_patterns=["tests/**/*.py", "pytest.ini", "pyproject.toml"],
                change_types={"testing"},
                min_magnitude=0.3,
                relevant_terms={"test", "testing", "unit", "integration"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "running_tests_locally": DocSectionTemplate(
            description="Commands and setup for executing tests on a dev machine",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["Makefile", "pytest.ini", "pyproject.toml"],
                change_types={"testing", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"test", "run", "local", "pytest"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "ci_test_workflow": DocSectionTemplate(
            description="How tests are run in CI, gating rules, and failure handling",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "tests/**/*.py"],
                change_types={"testing", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"ci", "test", "workflow", "automation"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "writing_new_tests": DocSectionTemplate(
            description="Guidelines and examples for authoring effective test cases",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["tests/**/*.py", "CONTRIBUTING.md"],
                change_types={"testing"},
                min_magnitude=0.3,
                relevant_terms={"test", "write", "guideline", "example"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "coverage_and_metrics": DocSectionTemplate(
            description="How to measure code coverage and interpret quality reports",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pytest.ini", "pyproject.toml", ".coveragerc"],
                change_types={"testing", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"coverage", "metric", "quality", "report"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "Makefile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"pipeline", "ci", "cd", "deployment"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "stage_definitions": DocSectionTemplate(
            description="Details on build, test, package, and deployment steps",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "Makefile"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.4,
                relevant_terms={"stage", "build", "package", "deploy"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "artifact_management": DocSectionTemplate(
            description="How build artifacts are versioned, stored, and retrieved",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "pyproject.toml"],
                change_types={"deployment", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"artifact", "version", "package", "storage"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "release_versioning": DocSectionTemplate(
            description="Semantic versioning rules and tagging strategy",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["pyproject.toml", "CHANGELOG.md"],
                change_types={"configuration"},
                min_magnitude=0.3,
                relevant_terms={"version", "release", "tag", "semver"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "rollback_strategy": DocSectionTemplate(
            description="Procedures for reverting a faulty deployment",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[".github/**/*.yml", "Makefile"],
                change_types={"deployment"},
                min_magnitude=0.3,
                relevant_terms={"rollback", "revert", "recovery", "deployment"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "changelog_format": DocSectionTemplate(
            description="Template and conventions for documenting release notes",
            themes=[SectionTheme.operational, SectionTheme.governance],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["CHANGELOG.md", "CONTRIBUTING.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"changelog", "release notes", "format", "template"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
