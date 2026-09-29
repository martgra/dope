# ruff: noqa: E501
"""Registered prompts for the changer service."""

from __future__ import annotations

from dope.prompts import Prompt, PromptRegistry

PromptRegistry.register(
    Prompt(
        name="change.system",
        version="v1",
        description="Production changer system prompt (initial version).",
        template="""
You are tasked to change the documentation for this application.

The scope of the documentation is to:
1. Give users a functional guide to how to use the application.
2. Give users a exemplified guide on how to set up the application.
3. Give users a understanding of how the application can be configured.

WORKFLOW
1. Read the documentation the user provides carefully. Make sure to understand it in context of the scope.
2. Review the suggested changes provided by the user.
3. Use the provided tool to get content of the code files.
4. Output only the full new documentation files.

TOOLS:
get_code_file_content: Load the content of code files as they are now to see specific details.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="change.system",
        version="v2-minimal",
        description=(
            "Tightened variant with explicit MINIMALITY (STRICT) clause. "
            "Marginal A/B win on the 17-fixture changer eval (see "
            "docs/wip/typesafe-jev-integration-plan.md for numbers)."
        ),
        template="""
You are tasked to change the documentation for this application.

The scope of the documentation is to:
1. Give users a functional guide to how to use the application.
2. Give users an exemplified guide on how to set up the application.
3. Give users an understanding of how the application can be configured.

WORKFLOW
1. Read the documentation the user provides carefully. Make sure to understand it in context of the scope.
2. Review the suggested changes provided by the user.
3. Use the provided tool to get content of the code files.
4. Output only the full new documentation file.

MINIMALITY (STRICT)
Make the smallest possible edit that satisfies the suggested changes.
- Preserve every line, sentence, and stylistic choice that the suggestion did NOT explicitly target — byte for byte, including punctuation, capitalization, whitespace, and the exact wording of examples, commands, and version strings.
- Do NOT rephrase, "improve", modernize, expand, or reorder content that was not part of the suggestion.
- Do NOT add explanatory prose beyond what the suggestion literally requires.
- If the suggestion is a bullet addition, add only that bullet in the requested position. Leave the surrounding bullets untouched.
- If the suggestion is a new section, add only that section. Do not restructure sibling sections.

TOOLS:
get_code_file_content: Load the content of code files as they are now to see specific details.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="change.user_template",
        version="v1",
        description="User-side template for the `change_existing` case.",
        template="""
Below is the content of file {doc_path}. Output only the changed file in full.
No explanation or additional content so that it can be pasted directly into the  {doc_path}.
Use the provided code tool to get more details about the code changes that justify the change. Use the paths from the provided list.

<content>
{doc_content}
</content>

<changes>
{changes_content}
</changes>
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="change.add_user_template",
        version="v1",
        description="User-side template for the `add` case (new doc file).",
        template="""
We suggest to add a new documentation file {doc_path} as the documentation is lacking.
Below are the suggested changes to create the new file.
Use the tool if you need to get more details about the code changes that justify the change. Use the paths from the provided list.

<changes>
{changes_content}
</changes>
""",
    )
)
