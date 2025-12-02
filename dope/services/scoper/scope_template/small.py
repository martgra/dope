from dope.models.domain.scope import (
    DocSectionTemplate,
    DocTemplate,
    FreshnessLevel,
    UpdateTriggers,
)
from dope.models.enums import DocTemplateKey, ProjectTier, SectionAudience, SectionTheme

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
            update_triggers=UpdateTriggers(
                code_patterns=["CONTRIBUTING.md", "README.md", ".github/*"],
                change_types={"documentation"},
                min_magnitude=0.3,
                relevant_terms={"contribution", "contribute", "community", "welcome"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "issue_reporting": DocSectionTemplate(
            description="How to file bugs or feature requests",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["CONTRIBUTING.md", ".github/ISSUE_TEMPLATE/*"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"issue", "bug", "feature request", "report", "template"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
        ),
        "pull_request_workflow": DocSectionTemplate(
            description="Branching conventions, PR etiquette, and review process",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=[
                    "CONTRIBUTING.md",
                    ".github/workflows/*",
                    ".github/PULL_REQUEST_TEMPLATE/*",
                ],
                change_types={"documentation", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"pull request", "pr", "review", "branch", "merge", "workflow"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "code_of_conduct": DocSectionTemplate(
            description="Community guidelines and expected behavior",
            themes=[SectionTheme.governance],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["CODE_OF_CONDUCT.md", "CONTRIBUTING.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"conduct", "behavior", "guideline", "community", "respect"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
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
            update_triggers=UpdateTriggers(
                code_patterns=["QUICKSTART.md", "pyproject.toml", "requirements.txt", "README.md"],
                change_types={"configuration", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"prerequisite", "requirement", "dependency", "tool", "version"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "installation": DocSectionTemplate(
            description="Step-by-step install instructions",
            themes=[SectionTheme.technical, SectionTheme.operational],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["QUICKSTART.md", "pyproject.toml", "setup.py", "Makefile"],
                change_types={"configuration", "deployment"},
                min_magnitude=0.3,
                relevant_terms={"install", "setup", "download", "build"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "first_run": DocSectionTemplate(
            description="Command or script to run first and expected output",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["QUICKSTART.md", "*/cli/*.py", "*/__main__.py"],
                change_types={"cli", "api", "feature"},
                min_magnitude=0.4,
                relevant_terms={"run", "start", "execute", "command", "output"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "verify_setup": DocSectionTemplate(
            description="How to confirm everything is working",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["QUICKSTART.md", "*/tests/*.py", "Makefile"],
                change_types={"testing", "configuration"},
                min_magnitude=0.3,
                relevant_terms={"verify", "test", "check", "validate", "confirm"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "next_steps": DocSectionTemplate(
            description="Links to deeper docs (API, examples, user guide)",
            themes=[SectionTheme.introductory],
            roles=[SectionAudience.engineering, SectionAudience.user],
            update_triggers=UpdateTriggers(
                code_patterns=["QUICKSTART.md", "docs/*", "README.md"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"next", "more", "advanced", "tutorial", "guide"},
            ),
            freshness_requirement=FreshnessLevel.LOW,
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
            update_triggers=UpdateTriggers(
                code_patterns=["examples/*", "EXAMPLES.md", "docs/examples/*"],
                change_types={"feature", "api", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"example", "demo", "sample", "recipe", "use case"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "basic_usage_snippet": DocSectionTemplate(
            description="Minimal code or command recipe for the most common task",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["examples/*", "*/cli/*.py", "*/api/*.py"],
                change_types={"api", "cli", "feature"},
                min_magnitude=0.4,
                relevant_terms={"basic", "simple", "minimal", "usage", "example"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "advanced_pattern": DocSectionTemplate(
            description="A more involved example showing best practices",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["examples/*", "*/core/*.py", "docs/examples/*"],
                change_types={"feature", "architecture", "api"},
                min_magnitude=0.4,
                relevant_terms={"advanced", "pattern", "best practice", "complex"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "troubleshooting_snippets": DocSectionTemplate(
            description="Small recipes for common pitfalls",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering, SectionAudience.support],
            update_triggers=UpdateTriggers(
                code_patterns=["examples/*", "docs/troubleshooting/*", "FAQ.md"],
                change_types={"bugfix", "documentation"},
                min_magnitude=0.3,
                relevant_terms={"troubleshoot", "error", "issue", "problem", "fix"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
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
            update_triggers=UpdateTriggers(
                code_patterns=["*/auth/*", "*/security/*", "*/api/*.py"],
                change_types={"api", "security", "feature"},
                min_magnitude=0.5,
                relevant_terms={"auth", "authenticate", "token", "key", "credential", "security"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "endpoints_overview": DocSectionTemplate(
            description="List of endpoints or entry-points with brief purposes",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*/api/*.py", "*/routes/*.py", "*/endpoints/*.py", "*/cli/*.py"],
                change_types={"api", "cli", "feature"},
                min_magnitude=0.4,
                relevant_terms={"endpoint", "route", "api", "function", "method"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "endpoint_details": DocSectionTemplate(
            description="For each endpoint: path, method, parameters, request/response schemas",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*/api/*.py", "*/routes/*.py", "*/models/*.py"],
                change_types={"api", "feature"},
                min_magnitude=0.5,
                relevant_terms={"parameter", "request", "response", "schema", "endpoint"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
        ),
        "data_models": DocSectionTemplate(
            description="Definitions of key objects (fields, types, required vs optional)",
            themes=[SectionTheme.technical, SectionTheme.introductory],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*/models/*.py", "*/schemas/*.py", "*/domain/*.py"],
                change_types={"api", "architecture", "feature"},
                min_magnitude=0.4,
                relevant_terms={"model", "schema", "field", "type", "data", "object"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "examples": DocSectionTemplate(
            description="Sample calls (curl/SDK) showing typical usage",
            themes=[SectionTheme.technical],
            roles=[SectionAudience.engineering],
            update_triggers=UpdateTriggers(
                code_patterns=["*/api/*.py", "examples/*", "docs/api/*"],
                change_types={"api", "feature", "documentation"},
                min_magnitude=0.4,
                relevant_terms={"example", "sample", "usage", "call", "request"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
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
            update_triggers=UpdateTriggers(
                code_patterns=["**/*.py", "**/*.ts", "**/*.js", "pyproject.toml"],
                change_types={"feature", "bugfix", "api", "architecture"},
                min_magnitude=0.3,
                relevant_terms={"change", "feature", "fix", "add", "remove", "update"},
            ),
            freshness_requirement=FreshnessLevel.HIGH,
        ),
        "version_history": DocSectionTemplate(
            description="Chronological list of past releases and their notes",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.management],
            update_triggers=UpdateTriggers(
                code_patterns=["CHANGELOG.md", "pyproject.toml"],
                change_types={"documentation"},
                min_magnitude=0.2,
                relevant_terms={"release", "version", "history"},
            ),
            freshness_requirement=FreshnessLevel.MEDIUM,
        ),
        "upgrade_notes": DocSectionTemplate(
            description="Any special migration or compatibility tips",
            themes=[SectionTheme.operational],
            roles=[SectionAudience.engineering, SectionAudience.support],
            update_triggers=UpdateTriggers(
                code_patterns=["*/migrations/*", "*/api/*.py", "pyproject.toml"],
                change_types={"api", "architecture", "configuration"},
                min_magnitude=0.5,
                relevant_terms={"breaking", "migration", "upgrade", "compatibility", "deprecated"},
            ),
            freshness_requirement=FreshnessLevel.CRITICAL,
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
