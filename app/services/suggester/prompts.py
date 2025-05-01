SUGGESTION_PROMPT = """
The provided scope to make decisions about code changes validate change in documentation.
<scope>
{scope}
<scope>

Summarization of the current documentation giving you an overview of the current state and content of the docs.
<current_documentation>
{documentation}
</current_documentation>

The code changes to suggest updates in the documentation on. If none of the code changes fit with the provided scope
and are deemed insiginificant do not suggest a change, else give a detailed instruction on the change needed based on
the code change, your understanding of the documentation and the scope.
<code_changes>
{code_changes}
</code_changes>
"""
FILE_SUMMARY_PROMPT = """

<{file_path}>
file_path: {file_path}

summary:
{summary}
</{file_path}>
"""
