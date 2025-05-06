from pathlib import Path

from platformdirs import user_cache_dir
from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.constants import DEFAULT_BRANCH, DOC_SUFFIX, EXCLUDE_DIRS
from app.models.enums import Provider
from app.models.internal import FileSuffix

APP_NAME = "dope"


class DocSettings(BaseModel):
    doc_filetypes: set[FileSuffix] = DOC_SUFFIX
    exclude_dirs: set[str] = EXCLUDE_DIRS
    docs_root: Path | None = None


class CodeRepoSettings(BaseModel):
    default_branch: str = DEFAULT_BRANCH
    code_repo_root: Path | None = None


class AgentSettings(BaseModel):
    provider: Provider = Provider.OPENAI
    token: SecretStr = Field(..., exclude=True)
    base_url: HttpUrl | None = None
    api_version: str = Field("2024-12-01-preview")

    @model_validator(mode="after")
    def validate_base_url_required_for_custom(self) -> "AgentSettings":
        if self.provider == Provider.AZURE and not self.base_url:
            raise ValueError(f"base_url must be provided when provider is {Provider.AZURE.value}")
        return self


class Settings(BaseSettings):
    state_directory: Path = Path(user_cache_dir(appname=APP_NAME))
    docs: DocSettings = DocSettings()
    git: CodeRepoSettings = CodeRepoSettings()
    agent: AgentSettings
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
