from pathlib import Path
from typing import Annotated

import typer

from app import settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.progress import track
from app.models.constants import DESCRIBE_CODE_STATE_FILENAME, DESCRIBE_DOCS_STATE_FILENAME
from app.services.describer.describer_agents import code_change_agent, doc_summarization_agent
from app.services.describer.describer_service import Scanner

app = typer.Typer()


@app.command()
def docs(
    docs_root: Annotated[Path, typer.Option("--root", help="Root of doc structure")] = Path("."),
):
    doc_scanner = Scanner(
        DocConsumer(
            docs_root,
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        doc_summarization_agent,
        state_filepath=settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME,
    )
    doc_state = doc_scanner.scan()
    try:
        for filepath, state_item in track(doc_state.items(), description="Describing doc changes."):
            doc_state[filepath] = doc_scanner.describe(file_path=filepath, state_item=state_item)
    finally:
        doc_scanner.save_state(doc_state)


@app.command()
def code(
    repo_root: Annotated[Path, typer.Option("--root", help="Root of code repo")] = Path("."),
    branch: Annotated[
        str, typer.Option("--branch", help="Branch to run againt")
    ] = settings.git.default_branch,
):
    code_scanner = Scanner(
        GitConsumer(repo_root, branch),
        code_change_agent,
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
