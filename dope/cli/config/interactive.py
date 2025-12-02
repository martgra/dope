"""Interactive configuration prompts using questionary.

DEPRECATED: This module is deprecated. Use dope.cli.ui.prompts instead.
Kept for backwards compatibility.
"""

from pathlib import Path

from pydantic import SecretStr

from dope.cli.ui.prompts import (
    handle_questionary_abort,
    validate_url,
)
from dope.cli.ui.prompts import (
    prompt_add_cache_to_git as _prompt_add_cache_to_git,
)
from dope.cli.ui.prompts import (
    prompt_code_repo_root as _prompt_code_repo_root,
)
from dope.cli.ui.prompts import (
    prompt_default_branch as _prompt_default_branch,
)
from dope.cli.ui.prompts import (
    prompt_deployment_endpoint as _prompt_deployment_endpoint,
)
from dope.cli.ui.prompts import (
    prompt_doc_root as _prompt_doc_root,
)
from dope.cli.ui.prompts import (
    prompt_doc_types as _prompt_doc_types,
)
from dope.cli.ui.prompts import (
    prompt_exclude_folders as _prompt_exclude_folders,
)
from dope.cli.ui.prompts import (
    prompt_provider as _prompt_provider,
)
from dope.cli.ui.prompts import (
    prompt_state_directory as _prompt_state_directory,
)
from dope.cli.ui.prompts import (
    prompt_token as _prompt_token,
)
from dope.models.enums import Provider
from dope.models.shared import FileSuffix

# Re-export for backwards compatibility
__all__ = [
    "handle_questionary_abort",
    "prompt_doc_root",
    "prompt_doc_types",
    "prompt_provider",
    "prompt_exclude_folders",
    "prompt_default_branch",
    "prompt_code_repo_root",
    "validate_url",
    "prompt_deployment_endpoint",
    "prompt_token",
    "prompt_state_directory",
    "prompt_add_cache_to_git",
]


def prompt_doc_root() -> Path:
    """Prompt for documentation root directory.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_doc_root() instead.
    """
    return _prompt_doc_root()


def prompt_doc_types() -> set[FileSuffix]:
    """Prompt for documentation file types.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_doc_types() instead.
    """
    return _prompt_doc_types()


def prompt_provider() -> Provider:
    """Prompt for LLM provider selection.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_provider() instead.
    """
    return _prompt_provider()


def prompt_exclude_folders(doc_root: Path) -> set[str]:
    """Prompt for folders to exclude from documentation scanning.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_exclude_folders() instead.
    """
    return _prompt_exclude_folders(doc_root)


def prompt_default_branch(repo_path: str) -> str:
    """Prompt for default Git branch selection.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_default_branch() instead.
    """
    return _prompt_default_branch(repo_path)


def prompt_code_repo_root() -> Path:
    """Prompt for code repository root directory.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_code_repo_root() instead.
    """
    return _prompt_code_repo_root()


def prompt_deployment_endpoint() -> str:
    """Prompt for Azure deployment URL.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_deployment_endpoint() instead.
    """
    return _prompt_deployment_endpoint()


def prompt_token() -> SecretStr:
    """Prompt for API token.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_token() instead.
    """
    return _prompt_token()


def prompt_state_directory() -> Path:
    """Prompt for state directory path.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_state_directory() instead.
    """
    return _prompt_state_directory()


def prompt_add_cache_to_git() -> bool:
    """Prompt whether to add cache directory to Git.

    DEPRECATED: Use dope.cli.ui.prompts.prompt_add_cache_to_git() instead.
    """
    return _prompt_add_cache_to_git()
