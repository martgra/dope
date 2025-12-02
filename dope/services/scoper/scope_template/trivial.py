from dope.models.domain.scope import (
    DocSectionTemplate,
    DocTemplate,
    FreshnessLevel,
    UpdateTriggers,
)
from dope.models.enums import DocTemplateKey, ProjectTier, SectionAudience, SectionTheme

TIERS = [
    ProjectTier.trivial,
    ProjectTier.small,
    ProjectTier.medium,
    ProjectTier.large,
    ProjectTier.massive,
]


readme_doc = DocTemplate(
    description="High-level project overview, installation instructions, and a basic example.",
    tiers=TIERS,
    sections={
        "project_overview": DocSectionTemplate(
            description="What the project does and why it exists",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering, SectionAudience.management, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "pyproject.toml", "*/__init__.py"],
                change_types={"architecture", "api", "feature"},
                min_magnitude=0.5,
                relevant_terms={"purpose", "mission", "overview", "what", "why", "features"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "quick_install": DocSectionTemplate(
            description="Minimal commands to install and run the project",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[
                    "pyproject.toml",
                    "requirements.txt",
                    "setup.py",
                    "Makefile",
                    "*/config/*",
                ],
                change_types={"configuration", "deployment"},
                min_magnitude=0.3,
                relevant_terms={
                    "install",
                    "setup",
                    "dependencies",
                    "requirements",
                    "prerequisites",
                },
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "hello_world_example": DocSectionTemplate(
            description="A simple code snippet or command showing basic usage",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["*/cli/*.py", "*/api/*.py", "*/__main__.py", "README.md"],
                change_types={"cli", "api", "feature"},
                min_magnitude=0.4,
                relevant_terms={"example", "usage", "quickstart", "hello", "demo", "tutorial"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "key_features": DocSectionTemplate(
            description="Bullet-list of the main capabilities",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.management, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "*/__init__.py", "*/core/*.py"],
                change_types={"feature", "api", "architecture"},
                min_magnitude=0.5,
                relevant_terms={"feature", "capability", "support", "functionality", "benefit"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "getting_help_and_support": DocSectionTemplate(
            description="Where to go when you have questions or issues",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["README.md", "CONTRIBUTING.md", ".github/*"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"support", "help", "issue", "question", "contact", "community"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "license_and_attribution": DocSectionTemplate(
            description="License terms and project credits",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.management, SectionAudience.compliance],
            update_triggers=UpdateTriggers(
                code_patterns=["LICENSE", "README.md", "pyproject.toml"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"license", "copyright", "attribution", "author", "contributor"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
    },
)

trivial = {DocTemplateKey.readme: readme_doc}
