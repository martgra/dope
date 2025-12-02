"""Factory for creating application services with proper dependency wiring."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dope.core.usage import UsageTracker
    from dope.models.settings import Settings
    from dope.services.changer.changer_service import DocsChanger
    from dope.services.describer.describer_base import CodeDescriberService, DescriberService
    from dope.services.scoper.scoper_service import ScopeService
    from dope.services.suggester.suggester_service import DocChangeSuggester


class ServiceFactory:
    """Factory for creating application services.

    This class encapsulates the dependency wiring logic for creating
    service instances, keeping CLI commands clean and focused on
    user interaction rather than service instantiation.

    Args:
        settings: Application settings containing configuration
    """

    def __init__(self, settings: "Settings"):
        """Initialize factory with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings

    def doc_scanner(
        self,
        root_path: Path,
        usage_tracker: "UsageTracker | None" = None,
    ) -> "DescriberService":
        """Create a DescriberService for documentation scanning.

        Args:
            root_path: Root path of documentation
            usage_tracker: Optional usage tracker

        Returns:
            Configured DescriberService instance
        """
        from dope.consumers.doc_consumer import DocConsumer
        from dope.repositories import DescriberRepository
        from dope.services.describer.describer_base import DescriberService

        consumer = DocConsumer(
            root_path,
            file_type_filter=self.settings.docs.doc_filetypes,
            exclude_dirs=self.settings.docs.exclude_dirs,
        )
        repository = DescriberRepository(self.settings.doc_state_path)
        return DescriberService(
            consumer=consumer,
            repository=repository,
            usage_tracker=usage_tracker,
            doc_term_index_path=self.settings.doc_terms_path,
        )

    def code_scanner(
        self,
        root_path: Path,
        branch: str,
        usage_tracker: "UsageTracker | None" = None,
    ) -> "CodeDescriberService":
        """Create a CodeDescriberService for code scanning.

        Args:
            root_path: Root path of code repository
            branch: Branch to compare against
            usage_tracker: Optional usage tracker

        Returns:
            Configured CodeDescriberService instance
        """
        from dope.consumers.git_consumer import GitConsumer
        from dope.repositories import DescriberRepository
        from dope.services.describer.describer_base import CodeDescriberService

        consumer = GitConsumer(root_path, branch)
        repository = DescriberRepository(self.settings.code_state_path)
        return CodeDescriberService(
            consumer=consumer,
            repository=repository,
            usage_tracker=usage_tracker,
            doc_term_index_path=self.settings.doc_terms_path,
        )

    def suggester(
        self,
        usage_tracker: "UsageTracker | None" = None,
    ) -> "DocChangeSuggester":
        """Create a DocChangeSuggester for generating suggestions.

        Loads scope template if available and creates scope-aware suggester.

        Args:
            usage_tracker: Optional usage tracker

        Returns:
            Configured DocChangeSuggester instance
        """
        from dope.repositories import SuggestionRepository
        from dope.services.suggester.suggester_service import DocChangeSuggester

        repository = SuggestionRepository(self.settings.suggestion_state_path)

        # Load scope if available
        scope = None
        if self.settings.scope_path.exists():
            try:
                from dope.core.config_io import load_scope_from_yaml

                scope = load_scope_from_yaml(self.settings.scope_path)
            except Exception:
                # Scope file exists but is invalid - continue without scope
                pass

        return DocChangeSuggester(
            repository=repository,
            scope=scope,
            scope_filter_settings=self.settings.scope_filter,
            usage_tracker=usage_tracker,
        )

    def docs_changer(
        self,
        root_path: Path,
        branch: str,
        usage_tracker: "UsageTracker | None" = None,
    ) -> "DocsChanger":
        """Create a DocsChanger for applying suggestions.

        Args:
            root_path: Root path for operations
            branch: Branch to compare against
            usage_tracker: Optional usage tracker

        Returns:
            Configured DocsChanger instance
        """
        from dope.consumers.doc_consumer import DocConsumer
        from dope.consumers.git_consumer import GitConsumer
        from dope.services.changer.changer_service import DocsChanger

        docs_consumer = DocConsumer(
            root_path,
            file_type_filter=self.settings.docs.doc_filetypes,
            exclude_dirs=self.settings.docs.exclude_dirs,
        )
        git_consumer = GitConsumer(root_path, branch)
        return DocsChanger(
            docs_consumer=docs_consumer,
            git_consumer=git_consumer,
            usage_tracker=usage_tracker,
        )

    def scope_service(
        self,
        root_path: Path,
        branch: str,
        usage_tracker: "UsageTracker | None" = None,
    ) -> "ScopeService":
        """Create a ScopeService for documentation scoping.

        Args:
            root_path: Root path for operations
            branch: Branch to compare against
            usage_tracker: Optional usage tracker

        Returns:
            Configured ScopeService instance
        """
        from dope.consumers.doc_consumer import DocConsumer
        from dope.consumers.git_consumer import GitConsumer
        from dope.services.scoper.scoper_service import ScopeService

        doc_consumer = DocConsumer(
            root_path,
            file_type_filter=self.settings.docs.doc_filetypes,
            exclude_dirs=self.settings.docs.exclude_dirs,
        )
        git_consumer = GitConsumer(root_path, branch)
        return ScopeService(
            doc_consumer=doc_consumer,
            git_consumer=git_consumer,
            usage_tracker=usage_tracker,
        )
