from pathlib import Path

import click

from app import settings
from app.cli.utils import show_full_output
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.constants import DESCRIBE_CODE_STATE_FILENAME, DESCRIBE_DOCS_STATE_FILENAME
from app.services.describer.describer_service import Scanner


@click.group(name="scan")
def scan():
    pass


@scan.command(name="docs")
@click.option("--docs-root", default=Path("."))
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def doc_scan(docs_root, output):
    scanner = Scanner(
        DocConsumer(
            docs_root,
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        None,
        state_filepath=settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME,
    )
    scan_data = scanner.scan()

    show_full_output(scan_data, output)


@scan.command(name="code")
@click.option("--repo-root", default=Path("."))
@click.option(
    "--branch", default=settings.git.default_branch, help="Branch to find changes against."
)
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def git_scan(repo_root, output, branch: str):
    scanner = Scanner(
        GitConsumer(repo_root, branch),
        None,
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )

    scan_data = scanner.scan()

    show_full_output(scan_data, output)
