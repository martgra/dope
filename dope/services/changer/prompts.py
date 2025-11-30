CHANGE_DOC_PROMPT = """
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
ADD_DOC_USER_PROMPT = """
We suggest to add a new documentation file {doc_path} as the documentation is lacking.
Below are the suggested changes to create the new file.
Use the tool if you need to get more details about the code changes that justify the change. Use the paths from the provided list.

<changes>
{changes_content}
</changes>
"""
