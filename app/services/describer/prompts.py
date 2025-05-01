DOC_DESCRIPTION_PROMPT = """
of the file. You are not allowed to fill information you cannot find from the content of the file.
If you cannot fill information just reply with None.

The File content will be provided within:

<Content>
file content
</Content>
"""
CODE_DESCRIPTION_PROMPT = """
Summarize the git diff. The summarization will be used for to decide if the documentation ought to
be updated based on a git diff. The description needs to be detailed enough to understand what to change in the doc,
and why it is important.
"""  # noqa: E501
SUMMARIZATION_TEMPLATE = """
file_path: {file_path}

<Content>
{content}
</Content>
"""
