"""Scan documentation and code for changes."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from dope.cli.common import command_context, get_branch_option
from dope.cli.ui import ProgressReporter, info, success, warning

app = typer.Typer(
    help="Scan documentation and code for changes",
    epilog="""
Examples:
  # Scan docs in current directory
  $ dope scan docs

  # Scan docs with higher concurrency
  $ dope scan docs --concurrency 10

  # Scan code changes against develop branch
  $ dope scan code --branch develop

  # Scan code with custom repo root
  $ dope scan code --root /path/to/repo --branch main
    """,
)

# Default concurrency for parallel LLM API calls
DEFAULT_CONCURRENCY = 5


@app.command()
def docs(
    docs_root: Annotated[
        Path, typer.Option("--root", help="Root directory of documentation")
    ] = Path("."),
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", help="Max parallel LLM calls")
    ] = DEFAULT_CONCURRENCY,
):
    """Scan documentation files for changes."""
    with command_context() as ctx:
        doc_scanner = ctx.factory.doc_scanner(docs_root, ctx.tracker)

        # Phase 1: Discover files and update state (hashes)
        info("Discovering documentation files...")
        state = doc_scanner.scan()
        total_files = len(state)
        success(f"Found {total_files} documentation files")

        # Phase 2: Generate summaries for files that need them (parallel)
        files_to_process = doc_scanner.files_needing_summary()
        if files_to_process:
            info(f"Generating summaries for {len(files_to_process)} files...")
            scan_with_progress = ProgressReporter.create_async_scanner(
                doc_scanner, files_to_process, "Scanning", concurrency
            )
            asyncio.run(scan_with_progress())
            success(f"Completed {len(files_to_process)} summaries")
        else:
            warning("All documentation files already processed")

        # Phase 3: Build term index for code scanning relevance
        doc_scanner.build_term_index()


@app.command()
def code(
    repo_root: Annotated[
        Path, typer.Option("--root", help="Root directory of code repository")
    ] = Path("."),
    branch: get_branch_option() = None,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", help="Max parallel LLM calls")
    ] = DEFAULT_CONCURRENCY,
):
    """Scan code changes against a branch."""
    with command_context(branch=branch) as ctx:
        code_scanner = ctx.factory.code_scanner(repo_root, ctx.branch, ctx.tracker)

        # Phase 1: Discover files, filter, and update state (hashes)
        info(f"Discovering code changes against branch '{ctx.branch}'...")
        state = code_scanner.scan()
        total_files = len(state)
        skipped_files = sum(1 for item in state.values() if item.get("skipped"))
        processable_files = total_files - skipped_files
        success(
            f"Found {total_files} changed files "
            f"({processable_files} to process, {skipped_files} skipped)"
        )

        # Phase 2: Generate summaries for files that need them (parallel)
        files_to_process = code_scanner.files_needing_summary()
        if files_to_process:
            info(f"Analyzing {len(files_to_process)} code changes...")
            scan_with_progress = ProgressReporter.create_async_scanner(
                code_scanner, files_to_process, "Scanning", concurrency
            )
            asyncio.run(scan_with_progress())
            success(f"Completed {len(files_to_process)} code analyses")
        else:
            warning("All code changes already analyzed")
