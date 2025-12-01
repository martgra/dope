"""Smart default configuration generation."""

from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from pydantic import HttpUrl, SecretStr

from dope.models.constants import DEFAULT_DOC_SUFFIX, EXCLUDE_DIRS
from dope.models.enums import Provider
from dope.models.settings import AgentSettings, CodeRepoSettings, DocSettings, Settings


def create_default_settings(provider: Provider, base_url: str | None, token: SecretStr) -> Settings:
    """Create settings with smart defaults based on current project.

    Args:
        provider: LLM provider to use
        base_url: Base URL for Azure provider (optional)
        token: API token for authentication

    Returns:
        Settings object with smart defaults
    """
    # Try to detect git repo
    try:
        repo = Repo(".", search_parent_directories=True)
        repo_root = Path(repo.working_tree_dir) if repo.working_tree_dir else Path.cwd()
        default_branch = str(repo.active_branch) if repo.active_branch else "main"
    except (InvalidGitRepositoryError, TypeError):
        repo_root = Path.cwd()
        default_branch = "main"

    return Settings(
        state_directory=Path(".dope"),
        docs=DocSettings(
            docs_root=repo_root,
            doc_filetypes=DEFAULT_DOC_SUFFIX,  # Just .md and .mdx
            exclude_dirs=EXCLUDE_DIRS,
        ),
        git=CodeRepoSettings(
            code_repo_root=repo_root,
            default_branch=default_branch,
        ),
        agent=AgentSettings(
            provider=provider,
            base_url=HttpUrl(base_url) if base_url else None,
            token=token,
        ),
    )
