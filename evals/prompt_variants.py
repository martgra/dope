# ruff: noqa: E501
"""Tightened prompt variants for A/B testing against the production prompts.

Each ``*_MINIMAL`` constant is a stricter version of the corresponding
production prompt in :mod:`dope.services.changer.prompts` /
:mod:`dope.services.scoper.prompts`. The tightening is uniform: bolt on
an explicit "make the smallest edit possible, preserve unrelated
content byte-for-byte" clause without changing the primary contract.

The variants are used by :mod:`evals.changer_prompt_ab` and
:mod:`evals.doc_aligner_prompt_ab` to compare production prompt vs
tightened prompt on the exact same fixture set. If a variant wins the
A/B decisively, promote it into the production prompts module.

Production prompts (verbatim, for reference):

* ``dope.services.changer.prompts.CHANGE_DOC_PROMPT``
* ``dope.services.scoper.prompts.ALIGN_DOC_PROMPT``
"""

from __future__ import annotations

CHANGE_DOC_PROMPT_MINIMAL = """
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
"""


ALIGN_DOC_PROMPT_MINIMAL = """
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
"""
