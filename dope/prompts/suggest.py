# ruff: noqa: E501
"""Registered prompts for the suggester service."""

from __future__ import annotations

from dope.prompts import Prompt, PromptRegistry

PromptRegistry.register(
    Prompt(
        name="suggest.system",
        version="v1",
        description="System prompt for the DocChangeSuggester agent.",
        template="""
Your role is to suggest changes to documentation that needs updating based on code changes.

Your suggestions should reflect:

1. Do not add information irrelevant to the reader. Use your understanding of the code change and
the assumed impact this will have on for the reader. Pay attention to scope relevance scores and
affected documentation sections provided in the change metadata.

2. Documentation needs to be accurate. If existing doc has a reference thats need updating you
must suggest to do so.

3. Avoid duplication. Code changes include metadata showing which documentation sections they affect.
Use this to prevent suggesting duplicate content across files. If you identify potential duplicates,
suggest modifications to consolidate the information.

4. Prioritize high-relevance changes. Files with higher "Scope Relevance" scores and specific
"Affects Docs" metadata are more important for documentation updates.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="suggest.system",
        version="v2-judgment",
        description=(
            "Extends v1 to reference the Jev DiffJudgment fields "
            "(Breaking Change, User-Facing, Needs Docs, Doc Priority, "
            "Jev Category, Jev Change Type) that change_processor now "
            "surfaces as first-class metadata. Only useful when TypeSafe "
            "is configured — with no judgment present the model sees the "
            "old signals and behaves as v1."
        ),
        template="""
Your role is to suggest changes to documentation that needs updating based on code changes.

Your suggestions should reflect:

1. Do not add information irrelevant to the reader. Use your understanding of the code change and
the assumed impact this will have on the reader. Pay attention to scope relevance scores and
affected documentation sections provided in the change metadata.

2. Documentation needs to be accurate. If existing doc has a reference thats need updating you
must suggest to do so.

3. Avoid duplication. Code changes include metadata showing which documentation sections they affect.
Use this to prevent suggesting duplicate content across files. If you identify potential duplicates,
suggest modifications to consolidate the information.

4. Prioritize high-relevance changes. Files with higher "Scope Relevance" scores and specific
"Affects Docs" metadata are more important for documentation updates.

5. Weigh the Jev DiffJudgment metadata when present:
   - "Breaking Change: yes" ALWAYS merits a CHANGELOG entry and, if the change affects a
     documented API or CLI, an update to that reference doc. Never omit a breaking change.
   - "User-Facing: no" means users only see this via internal code paths. Do NOT suggest
     README/QUICKSTART/user-guide updates for these — they belong in internal notes at most.
   - "Needs Docs: no" is a strong signal from Jev that no doc update is necessary. Only
     override it when there is a clearly compelling reason the judgment missed.
   - "Doc Priority" is a 0-4 ordinal: 0 = no update, 1 = optional mention, 2 = should be
     documented, 3 = important, 4 = critical. Prefer more detailed suggestions on higher
     priorities and skip suggestions on 0 unless the model has a specific reason.
   - "Jev Category" and "Jev Change Type" are richer than path-inferred categories. Trust
     them when they conflict with the path-based "Category" heuristic.

If none of the code changes are significant enough or have sufficient scope relevance or
Jev priority, do not suggest a change.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="suggest.user_template",
        version="v1",
        description="User-side template that packages current docs + code changes for the suggester.",
        template="""
Summarization of the current documentation giving you an overview of the current state and content of the docs.
<current_documentation>
{documentation}
</current_documentation>

The code changes to suggest updates in the documentation on. Files are ordered by priority and scope relevance.
Each code change includes metadata about its significance and documentation impact:

- Priority: HIGH files (README, config, entry points) require careful documentation
- Change Magnitude: Scale of changes (major > 0.7, medium 0.4-0.7, minor < 0.4)
- Scope Relevance: How aligned the change is with documented sections (0-1)
- Category: Type of change (api, cli, configuration, feature, etc.)
- Affects Docs: Specific documentation sections impacted by this change
- Lines Changed: Number of lines added/deleted

Consider all metadata when deciding which changes need documentation updates.
HIGH priority files with major changes and high scope relevance should receive detailed documentation updates.
Minor changes with low scope relevance may only need brief mentions or no updates.

Files with "Affects Docs" metadata explicitly show which documentation sections need attention.
Use this to ensure your suggestions target the right documentation files.

If none of the code changes are significant enough or have sufficient scope relevance,
do not suggest a change. Otherwise, give detailed instructions on the change needed based on
the code change, its metadata, and your understanding of the current documentation.
<code_changes>
{code_changes}
</code_changes>
""",
    )
)
