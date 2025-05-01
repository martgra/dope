from pathlib import Path

import click

from app import settings
from app.cli.utils import show_full_output
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.constants import DESCRIBE_CODE_STATE_FILENAME, DESCRIBE_DOCS_STATE_FILENAME
from app.services.describer.describer_agents import code_change_agent, doc_summarization_agent
from app.services.describer.describer_service import Scanner


@click.group(name="describe")
def describe():
    pass


@describe.command(name="docs")
@click.option("--docs-root", default=Path("."))
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def describe_docs(docs_root, output):
    doc_scanner = Scanner(
        DocConsumer(
            docs_root,
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        doc_summarization_agent,
        state_filepath=settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME,
    )
    describe_data = doc_scanner.describe()
    show_full_output(describe_data, output)


@describe.command(name="code")
@click.option("--repo-root", default=Path("."))
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
@click.option(
    "--branch", default=settings.git.default_branch, help="Branch to find changes against."
)
def describe_code_changes(repo_root, output, branch: str):
    code_scanner = Scanner(
        GitConsumer(repo_root, branch),
        code_change_agent,
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    describe_data = code_scanner.describe()
    show_full_output(describe_data, output)
