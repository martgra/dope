"""Documentation scope management commands."""

from pathlib import Path
from typing import Annotated

import questionary
import typer
import yaml
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn

from dope.cli.common import command_context, get_branch_option
from dope.models.domain.scope import (
    DocTemplate,
    ScopeTemplate,
)
from dope.models.enums import DocTemplateKey, ProjectTier
from dope.services.scoper.scope_template import get_scope

app = typer.Typer(
    help="Manage documentation structure",
    epilog="""
Examples:
  # Auto-detect project size and create scope
  $ dope scope create

  # Interactive mode - choose sections manually
  $ dope scope create --interactive

  # Specify project size
  $ dope scope create --project-size medium

  # Apply the created scope
  $ dope scope apply
    """,
)


def _prompt_project_size() -> ProjectTier | None:
    """Prompt interactively for project size.

    Returns:
        Selected ProjectTier, or None if user selected 'unsure'

    Raises:
        typer.Abort: If user cancels the selection
    """
    answer = questionary.select(
        "What's the project size?",
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
    """Prompt interactively to select documentation sections for a tier.

    Args:
        tier: Project tier to get documentation options for

    Returns:
        Dictionary of selected documentation templates

    Raises:
        typer.Abort: If user cancels the selection
    """
    options = get_scope(tier)
    choices = [
        questionary.Choice(
            title=f"{key.upper()}: {doc.description}",
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
    """Load the saved ScopeTemplate from disk.

    Args:
        state_path: Path to the state file

    Returns:
        Loaded ScopeTemplate

    Raises:
        typer.Abort: If loading fails
    """
    try:
        with state_path.open() as f:
            data = yaml.safe_load(f)
        return ScopeTemplate(**data)
    except (yaml.YAMLError, TypeError, FileNotFoundError) as e:
        print(f"Failed to load state from {state_path}: {e}")
        raise typer.Abort() from e


def _save_state(scope: ScopeTemplate, state_path: Path) -> None:
    """Save the ScopeTemplate to disk.

    Args:
        scope: ScopeTemplate to save
        state_path: Path to save the state file

    Raises:
        typer.Abort: If saving fails
    """
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
    service,
) -> ProjectTier:
    """Determine the project size from input, prompt, or automatic detection.

    Args:
        interactive: Whether to use interactive prompts
        project_size_input: Optional size string from CLI
        service: ScopeService for automatic detection

    Returns:
        Determined ProjectTier
    """
    size_enum = None

    # Try to parse from input
    if project_size_input:
        try:
            size_enum = ProjectTier(project_size_input)
        except ValueError:
            size_enum = None

    # Interactive prompt if needed
    if interactive and size_enum is None:
        size_enum = _prompt_project_size()

    # Automatic detection as fallback
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
    """Determine documentation sections from prompt or defaults.

    Args:
        interactive: Whether to use interactive selection
        size_enum: Project tier for default scope

    Returns:
        Dictionary of documentation templates
    """
    if interactive:
        return _prompt_docs_for_tier(size_enum)
    return get_scope(size_enum)


@app.command()
def create(
    interactive: Annotated[bool, typer.Option(help="Run interactive setup of scope")] = False,
    project_size: Annotated[
        str | None, typer.Option(help="Size of the project to create scope for")
    ] = None,
    branch: get_branch_option() = None,
):
    """Create or suggest a documentation scope and save it to state file."""
    with command_context(branch=branch) as ctx:
        state_path: Path = ctx.settings.scope_path
        service = ctx.factory.scope_service(Path("."), ctx.branch, ctx.tracker)

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


@app.command()
def apply(
    branch: get_branch_option() = None,
):
    """Apply the previously created documentation scope."""
    with command_context(branch=branch) as ctx:
        state_path: Path = ctx.settings.scope_path
        if not state_path.is_file():
            print(f"State file not found at {state_path}. Please run 'scope create' first.")
            raise typer.Abort()

        if not typer.confirm("Are you sure you want to apply the scoped changes?"):
            print("Aborted.")
            return

        service = ctx.factory.scope_service(Path("."), ctx.branch, ctx.tracker)
        scope_template = _load_state(state_path)

        try:
            service.apply_scope(scope_template)
        except Exception as e:
            print(f"Error applying scope: {e}")
            raise typer.Abort() from e

        print("Applied the structure.")
