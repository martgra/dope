DOC_DESCRIPTION_PROMPT = """
Your task is to fill information about a file in the documentation structure. You will be provided the scope and content for a particular file.
Based on the content of the file create a description of the documentation file. You are not allowed to fill information you cannot find from the content of the file.
If you cannot fill information just reply with None.

Your summary will be used to determine if code changes are relevant to the given file.

The user will provide you:
file_path: /path/to/doc

<Content>
file content
</Content>
"""


CODE_DESCRIPTION_PROMPT = """
Summarize the git diff.

The summarization will be used for to decide if documentation should be updated based on a git diff.
The description needs to be detailed enough to understand what to change in the doc,
and why it is important.

The user will provide you with git diffs like so.
file_path: /path/to/changed_file

<Content>
Git diff of given change.
</Content>
"""  # noqa: E501


SUMMARIZATION_TEMPLATE = """
file_path: {file_path}

<Content>
{content}
</Content>
"""
