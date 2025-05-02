from pathlib import Path

import click
import questionary
import yaml

from app import settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.domain.scope_template import (
    DocTemplate,
    DocTemplateKey,
    ProjectTier,
    ScopeTemplate,
)
from app.services.scoper.scope_template import get_scope
from app.services.scoper.scoper_service import ScopeService


def _init_scope_service(
    repo_path: Path = Path("."),
    branch: str = settings.git.default_branch,
    file_type_filter=None,
    exclude_dirs=None,
) -> ScopeService:
    """Initialize and return a ScopeService with configured DocConsumer and GitConsumer."""
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
        click.echo("Project size selection canceled.")
        raise click.Abort()
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
        click.echo("Documentation selection canceled.")
        raise click.Abort()
    return {key: options[key] for key in selected}


def _load_state(state_path: Path) -> ScopeTemplate:
    """Load the saved ScopeTemplate from disk; errors abort CLI."""
    try:
        with state_path.open() as f:
            data = yaml.safe_load(f)
        return ScopeTemplate(**data)
    except (yaml.YAMLError, TypeError, FileNotFoundError) as e:
        click.echo(f"Failed to load state from {state_path}: {e}")
        raise click.Abort() from e


def _save_state(scope: ScopeTemplate, state_path: Path) -> None:
    """Save the ScopeTemplate to disk; errors abort CLI."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with state_path.open("w") as f:
            yaml.dump(scope.model_dump(mode="json"), f, sort_keys=False, width=1000)
    except OSError as e:
        click.echo(f"Failed to save state to {state_path}: {e}")
        raise click.Abort() from e


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


@click.group(name="scope")
@click.option(
    "--state-file",
    envvar="SCOPE_STATE_FILE",
    type=click.Path(),
    help="Path to state file (overrides settings).",
)
@click.pass_context
def scope(ctx, state_file):
    """CLI group for documentation scope management."""
    ctx.obj = {}
    ctx.obj["state_path"] = (
        Path(state_file) if state_file else settings.state_directory / "scope.yaml"
    )


@scope.command(name="create")
@click.option(
    "--interactive",
    is_flag=True,
    default=False,
    help="Run in interactive prompt mode.",
)
@click.option(
    "--project-size",
    type=click.Choice([tier.value for tier in ProjectTier] + ["unsure"], case_sensitive=False),
    default=None,
    help="Size of project to determine documentation complexity.",
)
@click.option(
    "--branch",
    default=settings.git.default_branch,
    help="Git branch to diff against.",
)
@click.pass_context
def create(ctx, interactive: bool, project_size: str | None, branch: str):
    """Create or suggest a documentation scope and save it to state file."""
    state_path: Path = ctx.obj["state_path"]
    service = _init_scope_service(branch=branch)

    size_enum = _determine_project_size(interactive, project_size, service)
    doc_sections = _determine_doc_sections(interactive, size_enum)

    code_structure = service.get_code_overview()
    doc_files = service.get_doc_overview()

    scope_template = ScopeTemplate(
        size=size_enum,
        documentation_structure=doc_sections,
    )
    scope_template = service.suggest_structure(scope_template, doc_files, code_structure)

    _save_state(scope_template, state_path)
    click.echo(f"Scope created at {str(state_path)}")


@scope.command(name="apply")
@click.option(
    "--branch",
    default=settings.git.default_branch,
    help="Git branch to diff against.",
)
@click.pass_context
def apply(ctx, branch: str):
    """Apply the previously created documentation scope."""
    state_path: Path = ctx.obj["state_path"]
    if not state_path.is_file():
        click.echo(f"State file not found at {state_path}. Please run 'scope create' first.")
        raise click.Abort()
    if not click.confirm("Are you sure you want to apply the scoped changes?"):
        click.echo("Aborted.")
        return
    service = _init_scope_service(branch=branch)
    scope_template = _load_state(state_path)
    try:
        service.apply_scope(scope_template)
    except Exception as e:
        click.echo(f"Error applying scope: {e}")
        raise click.Abort() from e
    click.echo("Applied the structure.")
