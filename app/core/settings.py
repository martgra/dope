from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir
from pydantic import BaseModel, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.internal import FileSuffix

APP_NAME = "doc-scan"


class DocSettings(BaseModel):
    doc_filetypes: set[FileSuffix] = {".md", ".mdx"}
    exclude_dirs: set[str] = {"node_modules", ".venv", ".pytest_cache"}
    state_filepath: Path = Path(user_cache_dir(appname=APP_NAME)) / Path("doc-state.json")


class GitSettings(BaseModel):
    default_branch: str = "main"
    state_filepath: Path = Path(user_cache_dir(appname=APP_NAME)) / Path("git-state.json")


class SuggestionSettings(BaseModel):
    state_filepath: Path = Path(user_cache_dir(appname=APP_NAME)) / Path("suggestion-state.json")


class AgentSettings(BaseModel):
    token: SecretStr
    deployment_endpoint: HttpUrl
    api_version: str = Field("2024-12-01-preview")


class Settings(BaseSettings):
    config_dir: Path = Path(user_config_dir(APP_NAME))
    docs: DocSettings = DocSettings()
    git: GitSettings = GitSettings()
    suggestion: SuggestionSettings = SuggestionSettings()
    agent: AgentSettings
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
