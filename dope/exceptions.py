"""Custom exceptions for dope application.

This module provides a hierarchical exception structure for better error handling
and debugging throughout the dope application.
"""


class DopeError(Exception):
    """Base exception for all dope errors."""


class ConfigurationError(DopeError):
    """Base class for configuration-related errors."""


class ConfigNotFoundError(ConfigurationError):
    """Raised when configuration file cannot be found."""

    def __init__(self, search_paths: list[str] | None = None):
        """Initialize ConfigNotFoundError.

        Args:
            search_paths: List of paths searched for config file
        """
        self.search_paths = search_paths
        msg = "Configuration file not found"
        if search_paths:
            msg += f". Searched in: {', '.join(search_paths)}"
        super().__init__(msg)


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    def __init__(self, config_path: str, reason: str):
        """Initialize InvalidConfigError.

        Args:
            config_path: Path to the invalid config file
            reason: Explanation of why config is invalid
        """
        self.config_path = config_path
        self.reason = reason
        super().__init__(f"Invalid configuration in {config_path}: {reason}")


class GitError(DopeError):
    """Base class for git-related errors."""


class GitRepositoryNotFoundError(GitError):
    """Raised when git repository is not found."""

    def __init__(self, path: str):
        """Initialize GitRepositoryNotFoundError.

        Args:
            path: Path where git repository was expected
        """
        self.path = path
        super().__init__(f"Not a git repository: {path}")


class GitBranchNotFoundError(GitError):
    """Raised when git branch does not exist."""

    def __init__(self, branch: str, available_branches: list[str] | None = None):
        """Initialize GitBranchNotFoundError.

        Args:
            branch: Name of the branch that was not found
            available_branches: List of available branches
        """
        self.branch = branch
        self.available_branches = available_branches
        msg = f"Branch '{branch}' not found"
        if available_branches:
            branches_str = ", ".join(available_branches[:5])
            if len(available_branches) > 5:
                branches_str += f", ... ({len(available_branches) - 5} more)"
            msg += f". Available branches: {branches_str}"
        super().__init__(msg)


class DocumentError(DopeError):
    """Base class for document-related errors."""


class DocumentNotFoundError(DocumentError):
    """Raised when a document cannot be found."""

    def __init__(self, doc_path: str):
        """Initialize DocumentNotFoundError.

        Args:
            doc_path: Path to the document that was not found
        """
        self.doc_path = doc_path
        super().__init__(f"Document not found: {doc_path}")


class DirectoryError(DopeError):
    """Base class for directory-related errors."""


class InvalidDirectoryError(DirectoryError):
    """Raised when a path is not a valid directory."""

    def __init__(self, path: str, reason: str = "Not a directory"):
        """Initialize InvalidDirectoryError.

        Args:
            path: Path that is not a valid directory
            reason: Explanation of why path is invalid
        """
        self.path = path
        self.reason = reason
        super().__init__(f"{reason}: {path}")


class AgentError(DopeError):
    """Base class for LLM agent-related errors."""


class AgentNotConfiguredError(AgentError):
    """Raised when agent is not properly configured."""

    def __init__(
        self,
        message: str = "Agent configuration not found. Run 'dope config init' first.",
    ):
        """Initialize AgentNotConfiguredError.

        Args:
            message: Custom error message
        """
        super().__init__(message)


class ProviderError(AgentError):
    """Raised when LLM provider configuration is invalid."""

    def __init__(self, provider: str, reason: str):
        """Initialize ProviderError.

        Args:
            provider: Name of the LLM provider
            reason: Explanation of the configuration error
        """
        self.provider = provider
        self.reason = reason
        super().__init__(f"Provider '{provider}' configuration error: {reason}")


class InvalidSuffixError(DopeError):
    """Raised when a file suffix is invalid."""

    def __init__(self, suffix: str, reason: str = "Invalid suffix"):
        """Initialize InvalidSuffixError.

        Args:
            suffix: The invalid suffix
            reason: Explanation of why suffix is invalid
        """
        self.suffix = suffix
        self.reason = reason
        super().__init__(f"{reason}: {suffix}")


class SummaryGenerationError(AgentError):
    """Raised when summary generation fails."""

    def __init__(self, file_path: str, reason: str | None = None):
        """Initialize SummaryGenerationError.

        Args:
            file_path: Path to the file that failed
            reason: Explanation of the failure
        """
        self.file_path = file_path
        self.reason = reason
        msg = f"Failed to generate summary for {file_path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class ChangeMagnitudeError(GitError):
    """Raised when change magnitude calculation fails."""

    def __init__(self, file_path: str, reason: str | None = None):
        """Initialize ChangeMagnitudeError.

        Args:
            file_path: Path to the file that failed
            reason: Explanation of the failure
        """
        self.file_path = file_path
        self.reason = reason
        msg = f"Failed to calculate change magnitude for {file_path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class StateError(DopeError):
    """Base class for state-related errors."""


class StateLoadError(StateError):
    """Raised when state file cannot be loaded."""

    def __init__(self, state_path: str, reason: str | None = None):
        """Initialize StateLoadError.

        Args:
            state_path: Path to the state file
            reason: Explanation of the failure
        """
        self.state_path = state_path
        self.reason = reason
        msg = f"Failed to load state from {state_path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class StateSaveError(StateError):
    """Raised when state file cannot be saved."""

    def __init__(self, state_path: str, reason: str | None = None):
        """Initialize StateSaveError.

        Args:
            state_path: Path to the state file
            reason: Explanation of the failure
        """
        self.state_path = state_path
        self.reason = reason
        msg = f"Failed to save state to {state_path}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
