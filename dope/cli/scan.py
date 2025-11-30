"""Scan documentation and code for changes."""

from pathlib import Path
from typing import Annotated

import typer

from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.context import UsageContext
from dope.core.progress import track
from dope.core.utils import require_config
from dope.models.constants import DESCRIBE_CODE_STATE_FILENAME, DESCRIBE_DOCS_STATE_FILENAME
from dope.services.describer.describer_base import CodeDescriberService, DescriberService

app = typer.Typer(help="Scan documentation and code for changes")


@app.command()
def docs(
    docs_root: Annotated[
        Path, typer.Option("--root", help="Root directory of documentation")
    ] = Path("."),
):
    """Scan documentation files for changes."""
    settings = require_config()

    doc_scanner = DescriberService(
        DocConsumer(
            docs_root,
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        state_filepath=settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME,
    )
    doc_state = doc_scanner.scan()
    try:
        for filepath, state_item in track(
            doc_state.items(), description="Scanning documentation files"
        ):
            doc_state[filepath] = doc_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        doc_scanner.save_state(doc_state)
    UsageContext().log_usage()


@app.command()
def code(
    repo_root: Annotated[
        Path, typer.Option("--root", help="Root directory of code repository")
    ] = Path("."),
    branch: Annotated[str, typer.Option("--branch", "-b", help="Branch to compare against")] = None,
):
    """Scan code changes against a branch."""
    settings = require_config()

    # Use default branch if not specified
    if branch is None:
        branch = settings.git.default_branch

    code_scanner = CodeDescriberService(
        GitConsumer(repo_root, branch),
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    code_state = code_scanner.scan()
    try:
        for filepath, state_item in track(code_state.items(), description="Scanning code changes"):
            code_state[filepath] = code_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        code_scanner.save_state(code_state)
    UsageContext().log_usage()
