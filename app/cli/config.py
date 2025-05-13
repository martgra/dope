import functools
import sys
from pathlib import Path
from typing import Annotated

import questionary
import typer
from git import Repo
from pydantic import HttpUrl, SecretStr, ValidationError
from questionary import Choice
from rich import print

from app import get_settings
from app.core.settings import Settings
from app.core.utils import (
    generate_local_cache,
    generate_local_config_file,
    locate_local_config_file,
)
from app.models.constants import (
    CONFIG_FILENAME,
    DEFAULT_DOC_SUFFIX,
    DOC_SUFFIX,
    EXCLUDE_DIRS,
    LOCAL_CACHE_FOLDER,
)
from app.models.enums import Provider
from app.models.internal import FileSuffix

app = typer.Typer()


def handle_questionary_abort(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
        except Exception as err:
            raise err
        finally:
            if result is None:
                sys.exit(0)
        return result

    return wrapper


@handle_questionary_abort
def _set_doc_root() -> str:
    return Path(
        questionary.path(
            "Set path to doc rootfolder", only_directories=True, default=str(Path(".").resolve())
        ).ask()
    )


@handle_questionary_abort
def _set_doc_types() -> list[FileSuffix]:
    choices = [
        Choice(title=suffix, value=suffix, checked=suffix in DEFAULT_DOC_SUFFIX)
        for suffix in sorted(DOC_SUFFIX)
    ]

    return set(questionary.checkbox(message="Select doc filetypes.", choices=choices).ask())


@handle_questionary_abort
def _set_provider() -> Provider:
    return questionary.select(
        message="Which provider?",
        choices=[Choice(title=provider.value, value=provider) for provider in Provider],
    ).ask()


@handle_questionary_abort
def _set_exclude_folders(doc_root: Path) -> list[str]:
    doc_root = Path(doc_root)

    def _check_folder(file: Path):
        if file.name.startswith("."):
            return True
        if file.name in EXCLUDE_DIRS:
            return True

    choices = [
        Choice(title=file.name, value=file.name, checked=_check_folder(file))
        for file in doc_root.iterdir()
        if file.is_dir()
    ]
    if choices:
        return set(
            questionary.checkbox("Select folders to exclude from doc scan", choices=choices).ask()
        )
    return []


@handle_questionary_abort
def _set_default_branch(repo_path: str):
    repo = Repo(str(repo_path), search_parent_directories=True)
    branches = [str(branch) for branch in repo.branches]
    return questionary.select("Select default branch", choices=branches, default="main").ask()


@handle_questionary_abort
def _set_code_repo_root():
    suggested_root = Repo(".", search_parent_directories=True)
    return Path(
        questionary.path(
            "Set path to code root folder",
            only_directories=True,
            default=str(Path(suggested_root.working_dir).resolve()),
        ).ask()
    )


def _validate_url(text):
    try:
        # Will raise if not a valid URL
        HttpUrl(url=text)
        return True
    except ValidationError as e:
        # Extract the first error message
        msg = e.errors()[0]["msg"]
        return f"🚫 {msg}"


@handle_questionary_abort
def _set_deployment_endpoint():
    return questionary.text(message="Azure deployment url:", validate=_validate_url).ask()


@handle_questionary_abort
def _set_token():
    return SecretStr(questionary.password("Input token").ask())


@handle_questionary_abort
def _set_state_directory():
    cache_dir = Path(".") / Path(LOCAL_CACHE_FOLDER)
    return Path(questionary.path("Set state dir path", default=str(cache_dir.resolve())).ask())


@handle_questionary_abort
def _add_cache_dir_to_git():
    return questionary.confirm("Add cache dir to git?").ask()


def _verify_provider(provider: Provider, base_url: str | None) -> bool:
    if provider == Provider.AZURE:
        if not base_url:
            raise typer.BadParameter(
                f"Missing base url when provider is set to '{Provider.AZURE.value}'"
            )
        try:
            base_url = HttpUrl(base_url)
        except ValidationError as err:
            raise typer.BadParameter(f"{base_url} not valid url") from err
    return True


@app.command()
def show():
    settings = get_settings()
    print(settings.model_dump(mode="json"))


@app.command()
def init(
    all_default: Annotated[bool, typer.Option("--yes", help="All default values")] = False,
    force: Annotated[bool, typer.Option("--force", help="Override existing config")] = False,
    provider: Annotated[
        Provider, typer.Option(help="Choose LLM provider to use")
    ] = Provider.OPENAI,
    base_url: Annotated[
        str | None, typer.Option("--base-url", help="Deployment base url Azure")
    ] = None,
):
    """Initialize a YAML config file for Dope CLI."""
    _verify_provider(provider=provider, base_url=base_url)

    local_config_path = locate_local_config_file(CONFIG_FILENAME)
    cache_dir = generate_local_cache()
    new_settings = Settings()
    new_settings.state_directory = cache_dir
    new_settings.agent.provider = provider

    add_cache_to_git = False

    if not all_default:
        new_settings.state_directory = _set_state_directory()
        add_cache_to_git = _add_cache_dir_to_git()
        new_settings.git.code_repo_root = _set_code_repo_root()
        new_settings.git.default_branch = _set_default_branch(new_settings.git.code_repo_root)
        new_settings.docs.docs_root = Path(_set_doc_root())
        new_settings.docs.exclude_dirs = _set_exclude_folders(new_settings.docs.docs_root)
        new_settings.docs.doc_filetypes = _set_doc_types()
        new_settings.agent.provider = _set_provider()
        if new_settings.agent.provider == Provider.AZURE:
            new_settings.agent.base_url = _set_deployment_endpoint()
        else:
            new_settings.agent.base_url = None
        new_settings.agent.token = _set_token()
        force = typer.confirm(f"Config found at {local_config_path}. Overwrite?")
    if local_config_path and not force:
        typer.echo(f"Aborted – keeping existing config found at {local_config_path}.")
        raise typer.Exit()

    cache_dir = generate_local_cache(new_settings.state_directory, add_to_git=add_cache_to_git)
    generate_local_config_file(CONFIG_FILENAME, new_settings)
    raise typer.Exit()
