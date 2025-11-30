from dope.models.domain.scope_template import (
    DocSectionTemplate,
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    SectionAudience,
    SectionTheme,
)

TIERS = [ProjectTier.small, ProjectTier.medium, ProjectTier.large, ProjectTier.massive]

contributing_doc = DocTemplate(
    description="Guidelines for filing issues, proposing changes, and the pull-request process.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "purpose": DocSectionTemplate(
            description="Why contributions are welcome and what you can help with",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "issue_reporting": DocSectionTemplate(
            description="How to file bugs or feature requests",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "pull_request_workflow": DocSectionTemplate(
            description="Branching conventions, PR etiquette, and review process",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "code_of_conduct": DocSectionTemplate(
            description="Community guidelines and expected behavior",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.engineering],
        ),
    },
)

quickstart_doc = DocTemplate(
    description="A minimal set of steps to get the software installed and running quickly.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.user],
    sections={
        "prerequisites": DocSectionTemplate(
            description="What you need (tools, accounts, access) before you begin",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.user],
        ),
        "installation": DocSectionTemplate(
            description="Step-by-step install instructions",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
        ),
        "first_run": DocSectionTemplate(
            description="Command or script to run first and expected output",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.user],
        ),
        "verify_setup": DocSectionTemplate(
            description="How to confirm everything is working",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "next_steps": DocSectionTemplate(
            description="Links to deeper docs (API, examples, user guide)",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering, SectionAudience.user],
        ),
    },
)

examples_cookbook_doc = DocTemplate(
    description="A collection of code snippets and recipes demonstrating common use cases.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.user],
    sections={
        "overview": DocSectionTemplate(
            description="Catalog of available examples and what they demonstrate",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "basic_usage_snippet": DocSectionTemplate(
            description="Minimal code or command recipe for the most common task",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "advanced_pattern": DocSectionTemplate(
            description="A more involved example showing best practices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.management],
        ),
        "troubleshooting_snippets": DocSectionTemplate(
            description="Small recipes for common pitfalls",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.support],
        ),
    },
)

api_reference_doc = DocTemplate(
    description="Detailed descriptions of public APIs or library interfaces.",
    tiers=TIERS,
    roles=[SectionAudience.engineering],
    sections={
        "authentication": DocSectionTemplate(
            description="How to authenticate (tokens, keys, headers)",
            themes=[SectionTheme.technical, SectionTheme.governance],
            roles=[SectionAudience.engineering, SectionAudience.compliance],
        ),
        "endpoints_overview": DocSectionTemplate(
            description="List of endpoints or entry-points with brief purposes",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "endpoint_details": DocSectionTemplate(
            description="For each endpoint: path, method, parameters, request/response schemas",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
        "data_models": DocSectionTemplate(
            description="Definitions of key objects (fields, types, required vs optional)",
            themes=[SectionTheme.technical, SectionTheme.introductory],
            roles=[SectionAudience.engineering],
        ),
        "examples": DocSectionTemplate(
            description="Sample calls (curl/SDK) showing typical usage",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
        ),
    },
)

changelog_doc = DocTemplate(
    description="Chronological record of notable changes, releases, and upgrade notes.",
    tiers=TIERS,
    roles=[SectionAudience.engineering, SectionAudience.management],
    sections={
        "unreleased": DocSectionTemplate(
            description="List of changes pending the next release",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
        ),
        "version_history": DocSectionTemplate(
            description="Chronological list of past releases and their notes",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
        ),
        "upgrade_notes": DocSectionTemplate(
            description="Any special migration or compatibility tips",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.support],
        ),
    },
)


small = {
    DocTemplateKey.contributing: contributing_doc,
    DocTemplateKey.quickstart: quickstart_doc,
    DocTemplateKey.examples_cookbook: examples_cookbook_doc,
    DocTemplateKey.api_reference: api_reference_doc,
    DocTemplateKey.changelog: changelog_doc,
}
