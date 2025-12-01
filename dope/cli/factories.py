"""Factory functions for CLI service wiring.

This module provides factory functions that create properly configured
service instances, keeping the CLI commands clean and focused on
user interaction rather than dependency wiring.
"""

from pathlib import Path

from dope.cli.common import get_state_path
from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.usage import UsageTracker
from dope.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    DOC_TERM_INDEX_FILENAME,
    SUGGESTION_STATE_FILENAME,
)
from dope.models.settings import Settings
from dope.repositories import DescriberRepository, SuggestionRepository
from dope.services.describer.describer_base import CodeDescriberService, DescriberService
from dope.services.suggester.suggester_service import DocChangeSuggester


def create_git_consumer(
    root_path: Path,
    branch: str,
) -> GitConsumer:
    """Create a GitConsumer for code operations.

    Args:
        root_path: Root path of the repository
        branch: Branch to compare against

    Returns:
        Configured GitConsumer instance
    """
    return GitConsumer(root_path, branch)


def create_doc_consumer(
    root_path: Path,
    settings: Settings,
) -> DocConsumer:
    """Create a DocConsumer for documentation operations.

    Args:
        root_path: Root path of documentation
        settings: Application settings

    Returns:
        Configured DocConsumer instance
    """
    return DocConsumer(
        root_path,
        file_type_filter=settings.docs.doc_filetypes,
        exclude_dirs=settings.docs.exclude_dirs,
    )


def create_suggester(
    settings: Settings,
    usage_tracker: UsageTracker | None = None,
) -> DocChangeSuggester:
    """Create a DocChangeSuggester for generating suggestions.

    Args:
        settings: Application settings
        usage_tracker: Optional usage tracker

    Returns:
        Configured DocChangeSuggester instance
    """
    repository = SuggestionRepository(get_state_path(settings, SUGGESTION_STATE_FILENAME))
    return DocChangeSuggester(
        repository=repository,
        usage_tracker=usage_tracker,
    )


def create_doc_scanner(
    root_path: Path,
    settings: Settings,
    usage_tracker: UsageTracker | None = None,
) -> DescriberService:
    """Create a DescriberService for documentation scanning.

    Args:
        root_path: Root path of documentation
        settings: Application settings
        usage_tracker: Optional usage tracker

    Returns:
        Configured DescriberService instance
    """
    repository = DescriberRepository(get_state_path(settings, DESCRIBE_DOCS_STATE_FILENAME))
    return DescriberService(
        consumer=create_doc_consumer(root_path, settings),
        repository=repository,
        usage_tracker=usage_tracker,
        doc_term_index_path=get_state_path(settings, DOC_TERM_INDEX_FILENAME),
    )


def create_code_scanner(
    root_path: Path,
    branch: str,
    settings: Settings,
    usage_tracker: UsageTracker | None = None,
) -> CodeDescriberService:
    """Create a CodeDescriberService for code scanning.

    Args:
        root_path: Root path of code repository
        branch: Branch to compare against
        settings: Application settings
        usage_tracker: Optional usage tracker

    Returns:
        Configured CodeDescriberService instance
    """
    repository = DescriberRepository(get_state_path(settings, DESCRIBE_CODE_STATE_FILENAME))
    return CodeDescriberService(
        consumer=create_git_consumer(root_path, branch),
        repository=repository,
        usage_tracker=usage_tracker,
        doc_term_index_path=get_state_path(settings, DOC_TERM_INDEX_FILENAME),
    )


def create_docs_changer(
    root_path: Path,
    branch: str,
    settings: Settings,
    usage_tracker: UsageTracker | None = None,
):
    """Create a DocsChanger for applying suggestions.

    Args:
        root_path: Root path for operations
        branch: Branch to compare against
        settings: Application settings
        usage_tracker: Optional usage tracker

    Returns:
        Configured DocsChanger instance
    """
    from dope.services.changer.changer_service import DocsChanger

    return DocsChanger(
        docs_consumer=create_doc_consumer(root_path, settings),
        git_consumer=create_git_consumer(root_path, branch),
        usage_tracker=usage_tracker,
    )


def create_scope_service(
    root_path: Path,
    branch: str,
    settings: Settings,
    usage_tracker: UsageTracker | None = None,
):
    """Create a ScopeService for documentation scoping.

    Args:
        root_path: Root path for operations
        branch: Branch to compare against
        settings: Application settings
        usage_tracker: Optional usage tracker

    Returns:
        Configured ScopeService instance
    """
    from dope.services.scoper.scoper_service import ScopeService

    return ScopeService(
        doc_consumer=create_doc_consumer(root_path, settings),
        git_consumer=create_git_consumer(root_path, branch),
        usage_tracker=usage_tracker,
    )
