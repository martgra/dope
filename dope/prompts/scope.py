# ruff: noqa: E501, RUF001
"""Registered prompts for the scoper service."""

from __future__ import annotations

from dope.prompts import Prompt, PromptRegistry

PromptRegistry.register(
    Prompt(
        name="scope.complexity",
        version="v1",
        description="System prompt for the project-complexity classifier.",
        template="""
Your task is to determine the size and complexity of a code project.

We want to have 5 levels of complexity ranging from simple, low, medium, high, extreme.

The solution and code complexity level will be used as input to define scope of documentation. We assume that more complex code bases
will require more extensive documentation.

Assume that all code bases are of non-private. That means that simple will be some sort of published codebase.
Medium will be something that looks production grade and not a MVP while extreme is a large enterprise application.

Level | Key Characteristics | Typical Project Examples | Minimum Documentation
Simple | - < 1 K LoC- 1–2 modules- No external dependencies- Single‐dev- No CI/CD | "Hello, world" demosTiny scripts | README with setup & usage only
Low | - 1–10 K LoC- 3–5 modules- A handful of libs- Basic tests- Manual deploy | Small CLI toolsStatic sites | README + CONTRIBUTING + basic API reference
Medium | - 10–50 K LoC- 5–20 modules/services- Multiple libs- Automated tests & linting- CI | Mid-size web appsInternal tools | README + CONTRIBUTING + Architecture overview + Changelogs
High | - 50–200 K LoC- 20–50 modules/services- Distributed components- Performance & SLA targets | Public SaaS productsEnterprise apps | All of the above + Deployment guides + API & SDK docs
Extreme | - > 200 K LoC- 50+ modules/services- Multi-region/disaster-proof- Regulatory constraints | Banking systemsTelecom platforms | Full platform-level docs: onboarding, runbooks, run-cost guides, compliance manuals
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.creator",
        version="v1",
        description="System prompt for the scope-structure creator agent.",
        template="""
Your task is to look at the existing documentation, repo structure and code. Based on the provided
scope you are to map existing documentation to the new scope. Your output will be used to create or adjust the existing documentation.

Take into account information that you gain from the repo structure and doc structure to decide the best way to map the existing documentation to the new scope.
You can make assumptions about the tech stack and the repo structure based on the information that you have.

Return a dict of the form { section_key: file_path_to_the_implemented_section } where section_key is the key of the section in the scope and path_to_section is the path to the section in the documentation.
This dict will be used to create or adjust the existing documentation. You are allowed to create new files if you think that it is needed. You are also allowed to move files around if you think that it is needed.
You are also allowed to merge files if you think that it is needed. You are also allowed to create new directories if you think that it is needed.

This means that you can reorganize the scope to better fit the existing documentation. You can also create new documentation if you think that it is needed.
You can also suggest to move sections between documents if you think that it is needed. that should be reflected in the output. You can also merge documents from the
scope into one file if you think that it is needed. This could be due to factors of as the original repo structure, the original documentation structure or the
user input about the scope.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.align_doc",
        version="v1",
        description="Production doc-aligner system prompt (initial version).",
        template="""
Your task is to carefully review the provided file to check if it aligns with the provided scope.

You can:
1. Modify the file in place. The output should be the full file content.
2. Suggest that parts are out of scope are moved to other files that are better suited for the content
3. Parts that are added for moving to other files can be removed from the original file.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.align_doc",
        version="v2-minimal",
        description=(
            "Tightened aligner variant with explicit MINIMALITY (STRICT) clause. "
            "A/B on 7-fixture aligner eval: pass rate 91.4% -> 100.0%, "
            "content_similarity 0.583 -> 0.741, preserved_specifics 0.833 -> 1.00, "
            "at +9.2% cost. Promoted to production."
        ),
        template="""
Your task is to carefully review the provided file to check if it aligns with the provided scope.

You can:
1. Modify the file in place. The output should be the full file content.
2. Suggest that parts that are out of scope are moved to other files that are better suited for the content.
3. Parts that are added for moving to other files can be removed from the original file.

MINIMALITY (STRICT)
Make the smallest possible edit that brings the file into alignment with the scope.
- If the file already covers a scope-required section, DO NOT rewrite that section. Preserve its wording, structure, and stylistic choices byte for byte.
- Only ADD a section if the scope requires it and the file lacks it. Only MOVE content if it is clearly out of scope for this file per the scope description.
- Preserve every line the scope does not explicitly require you to touch, including exact command syntax, version strings, headings (even in unusual case), and the file's established tone.
- Do NOT expand terse sections, do NOT "improve" wording, do NOT add explanatory prose beyond what the scope specifically calls for.
- If the file is already fully aligned with the scope, return the file's content unchanged.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.change_file_user_template",
        version="v1",
        description="User-side template used by _modify_or_create_doc to align a single file to scope.",
        template="""
Here is the full scope of our documentation. This is just for reference and to
add TODOs if you belive content of the file is in the wrong file.
<scope>
{scope}
</scope>

Here is the filepath to the file we are changing.
<filepath>
{filepath}
<filepath>

Here is the content of the file. If the file is empty its fine. Just add section headers as
placeholders. Else reoder the content of the file.

<file_content>
{file_content}
</file_content>

Remember to only output the content that is to be written to the new file. We will use your output in place.
You are allowed to remove information from a file IF you add it for move to another file.
If you want to remove information and don't find a suitable place to move it to based on the provided scope,
you can add a TODO with instructions for manual review.
""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.complexity_user_template",
        version="v1",
        description="User-side template used by get_complexity to package repo metadata + structure.",
        template="""
repo metadata:
{metadata}

repo structure:
{structure}

""",
    )
)

PromptRegistry.register(
    Prompt(
        name="scope.move_content_user_template",
        version="v1",
        description="User-side template used by _implement_changes to move content between files.",
        template="""
You are moving content to this file as it did not align with the scope of the file it was found in.
Based on the instructions and the provided content to modify the file with, do changes in place in the
provided doc file.

The instructions provided based on reviewing the scope is:
<instructions>
{instructions}
</instructions>

<content to add>
{content}
</content to add>

<file content>
{doc_content}
</file content>
""",
    )
)
