"""Scan documentation and code for changes."""

from pathlib import Path
from typing import Annotated

import typer

from dope.cli.common import get_branch_option, resolve_branch
from dope.cli.factories import create_code_scanner, create_doc_scanner
from dope.core.progress import track
from dope.core.usage import UsageTracker
from dope.core.utils import require_config

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

    doc_scanner = create_doc_scanner(docs_root, settings, tracker)

    # Phase 1: Discover files and update state (hashes)
    doc_scanner.scan()

    # Phase 2: Generate summaries for files that need them
    files_to_process = doc_scanner.files_needing_summary()
    for filepath in track(files_to_process, description="Scanning documentation files"):
        doc_scanner.describe_and_save(filepath)

    # Phase 3: Build term index for code scanning relevance
    doc_scanner.build_term_index()

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

    code_scanner = create_code_scanner(repo_root, branch, settings, tracker)

    # Phase 1: Discover files, filter, and update state (hashes)
    code_scanner.scan()

    # Phase 2: Generate summaries for files that need them
    files_to_process = code_scanner.files_needing_summary()
    for filepath in track(files_to_process, description="Scanning code changes"):
        code_scanner.describe_and_save(filepath)

    tracker.log()
