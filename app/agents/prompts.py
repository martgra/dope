SUMMARIZATION_TEMPLATE = """
file_path: {file_path}

<Content>
{content}
</Content>
"""

SUGGESTION_PROMPT = """

<current_documentation>
{documentation}
</current_documentation>

<code_changes>
{code_changes}
</code_changes>
"""


ADD_DOC_USER_PROMPT = """
We suggest to add a new documentation file {doc_path} as the documentation is lacking.
Below are the suggested changes to create the new file.
Use the tool if you need to get more details about the code changes that justify the change. Use the paths from the provided list.

<changes>
{changes_content}
</changes>
"""

CHANGE_DOC_USER_PROMPT = """
Below is the content of file {doc_path}. Output only the changed file in full.
No explanation or additional content so that it can be pasted directly into the  {doc_path}.
Use the provided code tool to get more details about the code changes that justify the change. Use the paths from the provided list.

<content>
{doc_content}
</content>

<changes>
{changes_content}
</changes>
"""
