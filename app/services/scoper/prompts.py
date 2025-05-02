COMPLEXITY_DETERMINATION = """
Your task is to determine the size and complexity of a code project.

We want to have 5 levels of complexity ranging from simple, low, medium, high, extreme.

The solution and code complexity level will be used as input to define scope of documentation. We assume that more complex code bases
will require more extensive documentation.

Assume that all code bases are of non-private. That means that simple will be some sort of published codebase.
Medium will be something that looks production grade and not a MVP while extreme is a large enterprise application.

Level | Key Characteristics | Typical Project Examples | Minimum Documentation
Simple | - < 1 K LoC- 1–2 modules- No external dependencies- Single‐dev- No CI/CD | “Hello, world” demosTiny scripts | README with setup & usage only
Low | - 1–10 K LoC- 3–5 modules- A handful of libs- Basic tests- Manual deploy | Small CLI toolsStatic sites | README + CONTRIBUTING + basic API reference
Medium | - 10–50 K LoC- 5–20 modules/services- Multiple libs- Automated tests & linting- CI | Mid-size web appsInternal tools | README + CONTRIBUTING + Architecture overview + Changelogs
High | - 50–200 K LoC- 20–50 modules/services- Distributed components- Performance & SLA targets | Public SaaS productsEnterprise apps | All of the above + Deployment guides + API & SDK docs
Extreme | - > 200 K LoC- 50+ modules/services- Multi-region/disaster-proof- Regulatory constraints | Banking systemsTelecom platforms | Full platform-level docs: onboarding, runbooks, run-cost guides, compliance manuals
"""
CREATE_SCOPE_PROMPT = """
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
"""
ALIGN_DOC_PROMPT = """
Your task is to carefully review the provided file to check if it aligns with the provided scope.

You can:
1. Modify the file in place. The output should be the full file content.
2. Suggest that parts are out of scope are moved to other files that are better suited for the content
3. Parts that are added for moving to other files can be removed from the original file.
"""

CHANGE_FILE_PROMPT = """
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
"""
PROMPT = """
repo metadata:
{metadata}

repo structure:
{structure}

"""
MOVE_CONTENT_PROMPT = """
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
"""
