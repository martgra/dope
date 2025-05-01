import click
import questionary
import yaml

from app import settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.domain.scope_template import DocTemplate, DocTemplateKey, ProjectTier, ScopeTemplate
from app.services.scoper.scope_template import get_scope
from app.services.scoper.scoper_service import ScopeService


def _prompt_project_size():
    answer = questionary.select(
        "What’s the project size?",
        choices=[tier_size.value for tier_size in ProjectTier] + ["unsure"],
    ).ask()
    return answer if answer in ProjectTier else None


def _prompt_docs_for_tier(tier: ProjectTier):
    tier = ProjectTier(tier)
    options: dict[DocTemplateKey, DocTemplate] = get_scope(tier)

    choices = [
        questionary.Choice(
            title=f"{doc_key.value.upper()}: {doc.description}",
            value=doc_key,
            checked=True,
        )
        for doc_key, doc in options.items()
    ]

    selected: list[str | DocTemplateKey] = (
        questionary.checkbox(
            f"Select / Unselect documentation sections for the **{tier.value.capitalize()}** tier:",
            choices=choices,
        ).ask()
        or []
    )
    selected = {doc_key: options[doc_key] for doc_key in selected}
    return selected


@click.group(name="scope")
def scope():
    pass


@scope.command(name="create")
@click.option(
    "--interactive", is_flag=True, default=False, help="Run in fully interactive prompt mode."
)
@click.option(
    "--project-size",
    type=click.Choice(
        [tier_size.value for tier_size in ProjectTier] + ["usure"], case_sensitive=False
    ),
    default=None,
    help="Size of project to determine level of documentation complexity needed.",
)
@click.option("--apply", is_flag=True, default=False, help="Apply the structure.")
@click.option(
    "--branch", default=settings.git.default_branch, help="Branch to find changes against."
)
def create(interactive: bool, project_size: str, apply: bool, branch: str):
    scope_service = ScopeService(
        DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        GitConsumer(".", branch),
    )

    doc_structure = None
    try:
        project_size_enum = ProjectTier(project_size)
    except ValueError:
        project_size_enum = None

    if interactive:
        if project_size_enum is None:
            project_size_enum = _prompt_project_size()

        if project_size_enum in ProjectTier:
            doc_structure = _prompt_docs_for_tier(project_size_enum)

    code_structure = scope_service.get_code_overview()
    code_metadata = scope_service.get_metadata()
    doc_file_structure = scope_service.get_doc_overview()
    if project_size_enum not in ProjectTier:
        project_size_enum = scope_service.get_complexity(code_structure, code_metadata)
        doc_structure = get_scope(project_size_enum)

    state_path = settings.state_directory / "scope.yaml"

    if doc_structure and not state_path.is_file():
        doc_scope = ScopeTemplate(size=project_size_enum, documentation_structure=doc_structure)
        doc_scope = scope_service.suggest_structure(doc_scope, doc_file_structure, code_structure)
        with open(state_path, "w") as file:
            yaml.dump(doc_scope.model_dump(mode="json"), file, sort_keys=False, width=1000)

        click.echo(yaml.safe_dump(doc_scope.model_dump(mode="json"), sort_keys=False, width=1000))
    else:
        with state_path.open() as file:
            doc_scope = ScopeTemplate(**yaml.safe_load(file))
    if apply:
        scope_service.apply_scope(doc_scope)
        click.echo("Applied the structure.")
