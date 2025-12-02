"""CLI UI layer - presentation and user interaction abstractions."""

from dope.cli.ui.console import console, error, info, success, warning
from dope.cli.ui.formatters import ConfigFormatter, StatusFormatter
from dope.cli.ui.progress import ProgressReporter
from dope.cli.ui.prompts import (
    confirm,
    prompt_add_cache_to_git,
    prompt_code_repo_root,
    prompt_default_branch,
    prompt_deployment_endpoint,
    prompt_doc_root,
    prompt_doc_types,
    prompt_exclude_folders,
    prompt_provider,
    prompt_state_directory,
    prompt_token,
    select,
    text_input,
)

__all__ = [
    # Console
    "console",
    "info",
    "success",
    "warning",
    "error",
    # Progress
    "ProgressReporter",
    # Prompts
    "text_input",
    "select",
    "confirm",
    "prompt_doc_root",
    "prompt_doc_types",
    "prompt_provider",
    "prompt_exclude_folders",
    "prompt_default_branch",
    "prompt_code_repo_root",
    "prompt_deployment_endpoint",
    "prompt_token",
    "prompt_state_directory",
    "prompt_add_cache_to_git",
    # Formatters
    "ConfigFormatter",
    "StatusFormatter",
]
