"""Tests for custom exceptions."""

import pytest

from dope.exceptions import (
    AgentError,
    AgentNotConfiguredError,
    ChangeMagnitudeError,
    ConfigNotFoundError,
    ConfigurationError,
    DirectoryError,
    DocumentError,
    DocumentNotFoundError,
    DopeError,
    GitBranchNotFoundError,
    GitError,
    GitRepositoryNotFoundError,
    InvalidConfigError,
    InvalidDirectoryError,
    InvalidSuffixError,
    ProviderError,
    StateError,
    StateLoadError,
    StateSaveError,
    SummaryGenerationError,
)


def test_dope_error_is_base_exception():
    """Test that DopeError is base for all exceptions."""
    assert issubclass(ConfigurationError, DopeError)
    assert issubclass(GitError, DopeError)
    assert issubclass(DocumentError, DopeError)
    assert issubclass(DirectoryError, DopeError)
    assert issubclass(AgentError, DopeError)


def test_config_not_found_error_without_paths():
    """Test ConfigNotFoundError without search paths."""
    error = ConfigNotFoundError()
    assert error.search_paths is None
    assert str(error) == "Configuration file not found"


def test_config_not_found_error_with_search_paths():
    """Test ConfigNotFoundError with search paths."""
    paths = ["/path/1", "/path/2"]
    error = ConfigNotFoundError(search_paths=paths)
    assert error.search_paths == paths
    assert "/path/1" in str(error)
    assert "/path/2" in str(error)


def test_invalid_config_error():
    """Test InvalidConfigError includes path and reason."""
    error = InvalidConfigError("/config.yaml", "Missing required field 'api_key'")
    assert error.config_path == "/config.yaml"
    assert error.reason == "Missing required field 'api_key'"
    assert "/config.yaml" in str(error)
    assert "Missing required field" in str(error)


def test_git_repository_not_found_error():
    """Test GitRepositoryNotFoundError includes path."""
    error = GitRepositoryNotFoundError("/not/a/repo")
    assert error.path == "/not/a/repo"
    assert "/not/a/repo" in str(error)


def test_git_branch_not_found_error_without_available():
    """Test GitBranchNotFoundError without available branches."""
    error = GitBranchNotFoundError("feature")
    assert error.branch == "feature"
    assert error.available_branches is None
    assert "feature" in str(error)


def test_git_branch_not_found_error_with_available_branches():
    """Test GitBranchNotFoundError shows available branches."""
    branches = ["main", "dev", "staging"]
    error = GitBranchNotFoundError("feature", available_branches=branches)
    assert error.branch == "feature"
    assert error.available_branches == branches
    assert "main" in str(error)
    assert "dev" in str(error)


def test_git_branch_not_found_error_truncates_long_list():
    """Test GitBranchNotFoundError truncates long branch lists."""
    branches = [f"branch-{i}" for i in range(10)]
    error = GitBranchNotFoundError("feature", available_branches=branches)
    error_str = str(error)
    # Should show first 5 and indicate more
    assert "branch-0" in error_str
    assert "branch-4" in error_str
    assert "5 more" in error_str


def test_document_not_found_error():
    """Test DocumentNotFoundError includes document path."""
    error = DocumentNotFoundError("/docs/missing.md")
    assert error.doc_path == "/docs/missing.md"
    assert "/docs/missing.md" in str(error)


def test_invalid_directory_error_default_reason():
    """Test InvalidDirectoryError with default reason."""
    error = InvalidDirectoryError("/not/a/dir")
    assert error.path == "/not/a/dir"
    assert error.reason == "Not a directory"
    assert "/not/a/dir" in str(error)


def test_invalid_directory_error_custom_reason():
    """Test InvalidDirectoryError with custom reason."""
    error = InvalidDirectoryError("/path", "Directory is empty")
    assert error.path == "/path"
    assert error.reason == "Directory is empty"
    assert "Directory is empty" in str(error)


def test_agent_not_configured_error_default_message():
    """Test AgentNotConfiguredError with default message."""
    error = AgentNotConfiguredError()
    assert "Agent configuration not found" in str(error)
    assert "dope config init" in str(error)


def test_agent_not_configured_error_custom_message():
    """Test AgentNotConfiguredError with custom message."""
    custom_msg = "Custom agent error message"
    error = AgentNotConfiguredError(custom_msg)
    assert str(error) == custom_msg


def test_provider_error():
    """Test ProviderError includes provider and reason."""
    error = ProviderError("openai", "Invalid API key")
    assert error.provider == "openai"
    assert error.reason == "Invalid API key"
    assert "openai" in str(error)
    assert "Invalid API key" in str(error)


def test_invalid_suffix_error_default_reason():
    """Test InvalidSuffixError with default reason."""
    error = InvalidSuffixError(".bad")
    assert error.suffix == ".bad"
    assert error.reason == "Invalid suffix"
    assert ".bad" in str(error)


def test_invalid_suffix_error_custom_reason():
    """Test InvalidSuffixError with custom reason."""
    error = InvalidSuffixError(".xyz", "Suffix must be .md or .txt")
    assert error.suffix == ".xyz"
    assert error.reason == "Suffix must be .md or .txt"
    assert ".xyz" in str(error)
    assert "must be .md or .txt" in str(error)


def test_all_exceptions_catchable_as_dope_error():
    """Test all exceptions inherit from DopeError."""
    exceptions = [
        ConfigNotFoundError(),
        InvalidConfigError("path", "reason"),
        GitRepositoryNotFoundError("/path"),
        GitBranchNotFoundError("branch"),
        DocumentNotFoundError("/doc.md"),
        InvalidDirectoryError("/dir"),
        AgentNotConfiguredError(),
        ProviderError("provider", "reason"),
        InvalidSuffixError(".bad"),
        SummaryGenerationError("/file.py"),
        ChangeMagnitudeError("/file.py"),
        StateLoadError("/state.json"),
        StateSaveError("/state.json"),
    ]

    for exc in exceptions:
        assert isinstance(exc, DopeError)


def test_exception_hierarchy():
    """Test exception inheritance hierarchy is correct."""
    # Configuration exceptions
    assert issubclass(ConfigNotFoundError, ConfigurationError)
    assert issubclass(InvalidConfigError, ConfigurationError)
    assert issubclass(ConfigurationError, DopeError)

    # Git exceptions
    assert issubclass(GitRepositoryNotFoundError, GitError)
    assert issubclass(GitBranchNotFoundError, GitError)
    assert issubclass(ChangeMagnitudeError, GitError)
    assert issubclass(GitError, DopeError)

    # Document exceptions
    assert issubclass(DocumentNotFoundError, DocumentError)
    assert issubclass(DocumentError, DopeError)

    # Directory exceptions
    assert issubclass(InvalidDirectoryError, DirectoryError)
    assert issubclass(DirectoryError, DopeError)

    # Agent exceptions
    assert issubclass(AgentNotConfiguredError, AgentError)
    assert issubclass(ProviderError, AgentError)
    assert issubclass(SummaryGenerationError, AgentError)
    assert issubclass(AgentError, DopeError)

    # State exceptions
    assert issubclass(StateLoadError, StateError)
    assert issubclass(StateSaveError, StateError)
    assert issubclass(StateError, DopeError)

    # Other exceptions
    assert issubclass(InvalidSuffixError, DopeError)


def test_summary_generation_error_without_reason():
    """Test SummaryGenerationError without reason."""
    error = SummaryGenerationError("/path/to/file.py")
    assert error.file_path == "/path/to/file.py"
    assert error.reason is None
    assert "/path/to/file.py" in str(error)


def test_summary_generation_error_with_reason():
    """Test SummaryGenerationError with reason."""
    error = SummaryGenerationError("/path/to/file.py", "API rate limit exceeded")
    assert error.file_path == "/path/to/file.py"
    assert error.reason == "API rate limit exceeded"
    assert "/path/to/file.py" in str(error)
    assert "API rate limit exceeded" in str(error)


def test_change_magnitude_error_without_reason():
    """Test ChangeMagnitudeError without reason."""
    error = ChangeMagnitudeError("/path/to/file.py")
    assert error.file_path == "/path/to/file.py"
    assert error.reason is None
    assert "/path/to/file.py" in str(error)


def test_change_magnitude_error_with_reason():
    """Test ChangeMagnitudeError with reason."""
    error = ChangeMagnitudeError("/path/to/file.py", "Git diff failed")
    assert error.file_path == "/path/to/file.py"
    assert error.reason == "Git diff failed"
    assert "/path/to/file.py" in str(error)
    assert "Git diff failed" in str(error)


def test_state_load_error_without_reason():
    """Test StateLoadError without reason."""
    error = StateLoadError("/path/to/state.json")
    assert error.state_path == "/path/to/state.json"
    assert error.reason is None
    assert "/path/to/state.json" in str(error)


def test_state_load_error_with_reason():
    """Test StateLoadError with reason."""
    error = StateLoadError("/path/to/state.json", "Invalid JSON")
    assert error.state_path == "/path/to/state.json"
    assert error.reason == "Invalid JSON"
    assert "/path/to/state.json" in str(error)
    assert "Invalid JSON" in str(error)


def test_state_save_error_without_reason():
    """Test StateSaveError without reason."""
    error = StateSaveError("/path/to/state.json")
    assert error.state_path == "/path/to/state.json"
    assert error.reason is None
    assert "/path/to/state.json" in str(error)


def test_state_save_error_with_reason():
    """Test StateSaveError with reason."""
    error = StateSaveError("/path/to/state.json", "Permission denied")
    assert error.state_path == "/path/to/state.json"
    assert error.reason == "Permission denied"
    assert "/path/to/state.json" in str(error)
    assert "Permission denied" in str(error)
