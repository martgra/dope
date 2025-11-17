from pathlib import Path
from typing import Annotated

import questionary
import typer
import yaml
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.context import UsageContext
from app.core.utils import require_config
from app.models.domain.scope_template import (
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    ScopeTemplate,
)
from app.services.scoper.scope_template import get_scope
from app.services.scoper.scoper_service import ScopeService

app = typer.Typer(help="Manage documentation structure")


def _init_scope_service(
    repo_path: Path = Path("."),
    branch: str = None,
    file_type_filter=None,
    exclude_dirs=None,
) -> ScopeService:
    """Initialize and return a ScopeService with configured DocConsumer and GitConsumer."""
    settings = require_config()

    if branch is None:
        branch = settings.git.default_branch
    if file_type_filter is None:
        file_type_filter = settings.docs.doc_filetypes
    if exclude_dirs is None:
        exclude_dirs = settings.docs.exclude_dirs

    doc_consumer = DocConsumer(
        root_path=str(repo_path),
        file_type_filter=file_type_filter,
        exclude_dirs=exclude_dirs,
    )
    git_consumer = GitConsumer(root_path=str(repo_path), base_branch=branch)
    return ScopeService(doc_consumer, git_consumer)


def _prompt_project_size() -> ProjectTier:
    """Prompt interactively for project size; aborts if user cancels."""
    answer = questionary.select(
        "What’s the project size?",
        choices=[tier.value for tier in ProjectTier] + ["unsure"],
    ).ask()
    if answer is None:
        print("Project size selection canceled.")
        raise typer.Abort()
    try:
        return ProjectTier(answer)
    except ValueError:
        return None


def _prompt_docs_for_tier(tier: ProjectTier) -> dict[DocTemplateKey, DocTemplate]:
    """Prompt interactively to select documentation sections for a given tier; aborts on cancel."""
    options = get_scope(tier)
    choices = [
        questionary.Choice(
            title=f"{key.value.upper()}: {doc.description}",
            value=key,
            checked=True,
        )
        for key, doc in options.items()
    ]
    selected = questionary.checkbox(
        f"Select documentation sections for the {tier.value.capitalize()} tier:",
        choices=choices,
    ).ask()
    if selected is None:
        print("Documentation selection canceled.")
        raise typer.Abort()
    return {key: options[key] for key in selected}


def _load_state(state_path: Path) -> ScopeTemplate:
    """Load the saved ScopeTemplate from disk; errors abort CLI."""
    try:
        with state_path.open() as f:
            data = yaml.safe_load(f)
        return ScopeTemplate(**data)
    except (yaml.YAMLError, TypeError, FileNotFoundError) as e:
        print(f"Failed to load state from {state_path}: {e}")
        raise typer.Abort() from e


def _save_state(scope: ScopeTemplate, state_path: Path) -> None:
    """Save the ScopeTemplate to disk; errors abort CLI."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w") as f:
            yaml.dump(scope.model_dump(mode="json"), f, sort_keys=False, width=1000)
    except OSError as e:
        print(f"Failed to save state to {state_path}: {e}")
        raise typer.Abort() from e


def _determine_project_size(
    interactive: bool,
    project_size_input: str | None,
    service: ScopeService,
) -> ProjectTier:
    """Determine the project size enum: from input, interactive prompt, or automatic detection."""
    size_enum = None
    if project_size_input:
        try:
            size_enum = ProjectTier(project_size_input)
        except ValueError:
            size_enum = None
    if interactive and size_enum is None:
        size_enum = _prompt_project_size()
    if size_enum is None:
        code_structure = service.get_code_overview()
        code_metadata = service.get_metadata()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Determining project size...", total=None)
            size_enum = service.get_complexity(code_structure, code_metadata)
    return size_enum


def _determine_doc_sections(
    interactive: bool,
    size_enum: ProjectTier,
) -> dict[DocTemplateKey, DocTemplate]:
    """Determine documentation sections: interactive selection or default scope."""
    if interactive:
        return _prompt_docs_for_tier(size_enum)
    return get_scope(size_enum)


@app.command()
def create(
    interactive: Annotated[bool, typer.Option(help="Run interactive setup of scope")] = False,
    project_size: Annotated[
        str | None, typer.Option(help="Size of the project to create scope for")
    ] = None,
    branch: Annotated[
        str, typer.Option("--branch", "-b", help="Branch to compare against")
    ] = None,
):
    """Create or suggest a documentation scope and save it to state file."""
    settings = require_config()

    state_path: Path = settings.state_directory / "scope.yaml"
    service = _init_scope_service(branch=branch)

    size_enum = _determine_project_size(interactive, project_size, service)
    doc_sections = _determine_doc_sections(interactive, size_enum)

    code_structure = service.get_code_overview()
    doc_files = service.get_doc_overview()

    scope_template = ScopeTemplate(
        size=size_enum,
        documentation_structure=doc_sections,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Generating suggestion scope...", total=None)
        scope_template = service.suggest_structure(scope_template, doc_files, code_structure)
    _save_state(scope_template, state_path)
    print(f"Scope created at {str(state_path)}")
    UsageContext().log_usage()


@app.command()
def apply(
    branch: Annotated[
        str,
        typer.Option("--branch", "-b", help="Branch to compare against"),
    ] = None,
):
    """Apply the previously created documentation scope."""
    settings = require_config()

    state_path: Path = settings.state_directory / "scope.yaml"
    if not state_path.is_file():
        print(f"State file not found at {state_path}. Please run 'scope create' first.")
        raise typer.Abort()
    if not typer.confirm("Are you sure you want to apply the scoped changes?"):
        print("Aborted.")
        return
    service = _init_scope_service(branch=branch)
    scope_template = _load_state(state_path)
    try:
        service.apply_scope(scope_template)
    except Exception as e:
        print(f"Error applying scope: {e}")
        raise typer.Abort() from e
    print("Applied the structure.")
    UsageContext().log_usage()
