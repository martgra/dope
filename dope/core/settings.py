from pathlib import Path

from platformdirs import user_cache_dir
from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dope.models.constants import DEFAULT_BRANCH, DOC_SUFFIX, EXCLUDE_DIRS
from dope.models.enums import Provider
from dope.models.internal import FileSuffix

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


class Settings(BaseSettings):
    """Main application settings."""

    state_directory: Path = Path(user_cache_dir(appname=APP_NAME))
    docs: DocSettings = DocSettings()
    git: CodeRepoSettings = CodeRepoSettings()
    agent: AgentSettings | None = None
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
