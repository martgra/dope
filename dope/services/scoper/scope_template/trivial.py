from dope.models.domain.scope_template import (
    DocSectionTemplate,
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)

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
        ),
        "quick_install": DocSectionTemplate(
            description="Minimal commands to install and run the project",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "hello_world_example": DocSectionTemplate(
            description="A simple code snippet or command showing basic usage",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.user],
        ),
        "key_features": DocSectionTemplate(
            description="Bullet-list of the main capabilities",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.management, SectionAudience.user],
        ),
        "getting_help_and_support": DocSectionTemplate(
            description="Where to go when you have questions or issues",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.user],
        ),
        "license_and_attribution": DocSectionTemplate(
            description="License terms and project credits",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.management, SectionAudience.compliance],
        ),
    },
)

trivial = {DocTemplateKey.readme: readme_doc}
