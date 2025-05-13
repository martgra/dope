from pathlib import Path
from typing import Annotated

import typer

from app import get_settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.context import UsageContext
from app.core.progress import track
from app.models.constants import DESCRIBE_CODE_STATE_FILENAME, DESCRIBE_DOCS_STATE_FILENAME
from app.services.describer.describer_base import CodeDescriberService, DescriberService

app = typer.Typer()


@app.command()
def docs(
    docs_root: Annotated[Path, typer.Option("--root", help="Root of doc structure")] = None,
):
    settings = get_settings()
    docs_root = docs_root or settings.docs.docs_root

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
        for filepath, state_item in track(doc_state.items(), description="Describing doc changes."):
            doc_state[filepath] = doc_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        doc_scanner.save_state(doc_state)
    UsageContext().log_usage()


@app.command()
def code(
    repo_root: Annotated[Path, typer.Option("--root", help="Root of code repo")] = Path("."),
    branch: Annotated[str, typer.Option("--branch", help="Branch to run againt")] = None,
):
    settings = get_settings()
    code_scanner = CodeDescriberService(
        GitConsumer(repo_root, branch),
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    code_state = code_scanner.scan()
    try:
        for filepath, state_item in track(
            code_state.items(), description="Describing code changes"
        ):
            code_state[filepath] = code_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        code_scanner.save_state(code_state)
    UsageContext().log_usage()
