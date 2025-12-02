"""Pydantic models for application settings."""

from functools import lru_cache
from pathlib import Path

from platformdirs import user_cache_dir
from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dope.models.constants import DEFAULT_BRANCH, DOC_SUFFIX, EXCLUDE_DIRS
from dope.models.enums import Provider
from dope.models.shared import FileSuffix

APP_NAME = "dope"


class DocSettings(BaseModel):
    """Settings for documentation processing."""

    doc_filetypes: set[FileSuffix] = DOC_SUFFIX
    exclude_dirs: set[str] = EXCLUDE_DIRS
    docs_root: Path | None = None


class CodeRepoSettings(BaseModel):
    """Settings for code repository configuration."""

    default_branch: str = DEFAULT_BRANCH
    code_repo_root: Path | None = None


class AgentSettings(BaseModel):
    """Settings for LLM agent configuration."""

    provider: Provider = Provider.OPENAI
    token: SecretStr = Field(..., exclude=True)
    base_url: HttpUrl | None = None
    api_version: str = Field("2024-12-01-preview")

    @model_validator(mode="after")
    def validate_base_url_required_for_custom(self) -> "AgentSettings":
        """Validate that base_url is provided for Azure provider."""
        if self.provider == Provider.AZURE and not self.base_url:
            raise ValueError(f"base_url must be provided when provider is {Provider.AZURE.value}")
        return self


class ScopeFilterSettings(BaseModel):
    """Settings for scope-based change filtering.

    Controls how code changes are matched against scope section triggers.
    Weights determine contribution to overall relevance score (should sum to ~1.0).
    """

    pattern_match_weight: float = Field(
        default=0.4, description="Weight for matching code patterns (0-1)"
    )
    category_match_weight: float = Field(
        default=0.3, description="Weight for matching change categories (0-1)"
    )
    magnitude_weight: float = Field(default=0.3, description="Weight for change magnitude (0-1)")
    min_relevance_score: float = Field(
        default=0.3,
        description="Minimum relevance score (0-1) to include change in suggestions",
    )


class Settings(BaseSettings):
    """Main application settings.

    This class stores application configuration including paths,
    documentation settings, git settings, and LLM agent configuration.
    """

    state_directory: Path = Path(user_cache_dir(appname=APP_NAME))
    docs: DocSettings = DocSettings()
    git: CodeRepoSettings = CodeRepoSettings()
    agent: AgentSettings | None = None
    scope_filter: ScopeFilterSettings = ScopeFilterSettings()
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    # State file path properties
    @property
    def doc_state_path(self) -> Path:
        """Path to documentation state file."""
        from dope.models.constants import DESCRIBE_DOCS_STATE_FILENAME

        return self.state_directory / DESCRIBE_DOCS_STATE_FILENAME

    @property
    def code_state_path(self) -> Path:
        """Path to code state file."""
        from dope.models.constants import DESCRIBE_CODE_STATE_FILENAME

        return self.state_directory / DESCRIBE_CODE_STATE_FILENAME

    @property
    def suggestion_state_path(self) -> Path:
        """Path to suggestion state file."""
        from dope.models.constants import SUGGESTION_STATE_FILENAME

        return self.state_directory / SUGGESTION_STATE_FILENAME

    @property
    def doc_terms_path(self) -> Path:
        """Path to documentation terms index file."""
        from dope.models.constants import DOC_TERM_INDEX_FILENAME

        return self.state_directory / DOC_TERM_INDEX_FILENAME

    @property
    def scope_path(self) -> Path:
        """Path to scope configuration file."""
        return self.state_directory / "scope.yaml"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings.

    This function loads settings from configuration files (local or global) on first call,
    then returns the cached instance on subsequent calls. This pattern:
    - Avoids circular import issues by deferring imports until function call
    - Prevents repeated file I/O and YAML parsing
    - Makes testing easier (can clear cache with get_settings.cache_clear())
    - Provides single source of truth for settings access

    Returns:
        Settings: The cached settings instance.

    Raises:
        SystemExit: If configuration file exists but is invalid.

    Example:
        >>> settings = get_settings()
        >>> settings.agent.provider
        Provider.OPENAI
    """
    from dope.core.config_io import load_settings_from_yaml
    from dope.core.config_locator import locate_global_config, locate_local_config_file
    from dope.models.constants import CONFIG_FILENAME

    config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(
        CONFIG_FILENAME
    )

    # Always create settings object - agent will be None if no config
    settings = Settings()
    if config_filepath:
        try:
            settings = Settings(**load_settings_from_yaml(config_filepath))
        except Exception as e:
            # Config exists but is invalid - this is an error
            from dope.exceptions import ConfigurationError

            raise ConfigurationError(f"Config file invalid: {config_filepath}\nError: {e}") from e

    return settings
