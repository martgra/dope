"""Scan documentation and code for changes."""

from pathlib import Path
from typing import Annotated

import typer

from dope.cli.common import get_branch_option, get_state_path, resolve_branch
from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.progress import track
from dope.core.usage import UsageTracker
from dope.core.utils import require_config
from dope.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    DOC_TERM_INDEX_FILENAME,
)
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
    tracker = UsageTracker()

    doc_scanner = DescriberService(
        DocConsumer(
            docs_root,
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        state_filepath=get_state_path(settings, DESCRIBE_DOCS_STATE_FILENAME),
        usage_tracker=tracker,
        doc_term_index_path=get_state_path(settings, DOC_TERM_INDEX_FILENAME),
    )
    doc_state = doc_scanner.scan()
    try:
        for filepath, state_item in track(
            doc_state.items(), description="Scanning documentation files"
        ):
            doc_state[filepath] = doc_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        doc_scanner.save_state(doc_state)
    tracker.log()


@app.command()
def code(
    repo_root: Annotated[
        Path, typer.Option("--root", help="Root directory of code repository")
    ] = Path("."),
    branch: get_branch_option() = None,
):
    """Scan code changes against a branch."""
    settings = require_config()
    branch = resolve_branch(branch, settings)
    tracker = UsageTracker()

    code_scanner = CodeDescriberService(
        GitConsumer(repo_root, branch),
        state_filepath=get_state_path(settings, DESCRIBE_CODE_STATE_FILENAME),
        usage_tracker=tracker,
        doc_term_index_path=get_state_path(settings, DOC_TERM_INDEX_FILENAME),
    )
    code_state = code_scanner.scan()
    try:
        for filepath, state_item in track(code_state.items(), description="Scanning code changes"):
            code_state[filepath] = code_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        code_scanner.save_state(code_state)
    tracker.log()
