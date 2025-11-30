from dope.models.shared import FileSuffix

SUGGESTION_STATE_FILENAME: str = "suggestion-state.json"
DESCRIBE_DOCS_STATE_FILENAME: str = "doc-state.json"
DESCRIBE_CODE_STATE_FILENAME: str = "git-state.json"

LOCAL_CACHE_FOLDER: str = ".dope"
CONFIG_FILENAME: str = ".doperc.yaml"
APP_NAME: str = "dope"

DOC_SUFFIX: set[FileSuffix] = {
    FileSuffix(".md"),
    FileSuffix(".markdown"),
    FileSuffix(".mdx"),
    FileSuffix(".rst"),
    FileSuffix(".adoc"),
    FileSuffix(".asciidoc"),
    FileSuffix(".org"),
    FileSuffix(".wiki"),
}

DEFAULT_DOC_SUFFIX: set[FileSuffix] = {FileSuffix(".md"), FileSuffix(".mdx")}

EXCLUDE_DIRS: set[str] = {"node_modules", ".venv", ".pytest_cache", "dist", "build", "venv"}

DEFAULT_BRANCH: str = "main"
