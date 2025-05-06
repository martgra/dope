from app.models.internal import FileSuffix

SUGGESTION_STATE_FILENAME: str = "suggestion-state.json"
DESCRIBE_DOCS_STATE_FILENAME: str = "doc-state.json"
DESCRIBE_CODE_STATE_FILENAME: str = "git-state.json"

LOCAL_CACHE_FOLDER: str = ".dope"
CONFIG_FILENAME: str = ".doperc.yaml"
APP_NAME: str = "dope"

DOC_SUFFIX: set[FileSuffix] = {
    ".md",
    ".markdown",
    ".mdx",
    ".rst",
    ".adoc",
    ".asciidoc",
    ".org",
    ".wiki",
}

DEFAULT_DOC_SUFFIX: set[FileSuffix] = {".md", ".mdx"}

EXCLUDE_DIRS: set[str] = {"node_modules", ".venv", ".pytest_cache", "dist", "build", "venv"}

DEFAULT_BRANCH: str = "main"
