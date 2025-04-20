from pathlib import Path

import click

from app import settings
from app.agents.code_change_analyzer import code_change_agent
from app.agents.docs_analyzer import doc_summarization_agent
from app.cli.utils import show_full_output
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.services.scanner import Scanner


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
        state_filepath=settings.docs.state_filepath,
    )
    describe_data = doc_scanner.describe()
    show_full_output(describe_data, output)


@describe.command(name="code")
@click.option("--repo-root", default=Path("."))
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def describe_code_changes(repo_root, output):
    code_scanner = Scanner(
        GitConsumer(repo_root, settings.git.default_branch),
        code_change_agent,
        state_filepath=settings.git.state_filepath,
    )
    describe_data = code_scanner.describe()
    show_full_output(describe_data, output)
