"""Scan documentation and code for changes."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskProgressColumn, TextColumn

from dope.cli.common import command_context, get_branch_option

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
        rprint("[cyan]→ Discovering documentation files...[/cyan]")
        state = doc_scanner.scan()
        total_files = len(state)
        rprint(f"[green]✓ Found {total_files} documentation files[/green]")

        # Phase 2: Generate summaries for files that need them (parallel)
        files_to_process = doc_scanner.files_needing_summary()
        if files_to_process:
            rprint(f"[cyan]→ Generating summaries for {len(files_to_process)} files...[/cyan]")
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task("Scanning", total=len(files_to_process))

                # Run with progress updates
                async def scan_with_progress():
                    state = doc_scanner._load_state()
                    semaphore = asyncio.Semaphore(concurrency)

                    async def process_file(file_path: str):
                        async with semaphore:
                            state_item = state.get(file_path, {}).copy()
                            if not state_item.get("skipped") and not state_item.get("summary"):
                                updated = await doc_scanner.describe_async(file_path, state_item)
                                state[file_path] = updated
                            progress.update(task, advance=1)

                    tasks = [process_file(fp) for fp in files_to_process]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    doc_scanner._save_state(state)

                asyncio.run(scan_with_progress())
            rprint(f"[green]✓ Completed {len(files_to_process)} summaries[/green]")
        else:
            rprint("[yellow]✓ All documentation files already processed[/yellow]")

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
        rprint(f"[cyan]→ Discovering code changes against branch '{ctx.branch}'...[/cyan]")
        state = code_scanner.scan()
        total_files = len(state)
        skipped_files = sum(1 for item in state.values() if item.get("skipped"))
        processable_files = total_files - skipped_files
        rprint(
            f"[green]✓ Found {total_files} changed files "
            f"({processable_files} to process, {skipped_files} skipped)[/green]"
        )

        # Phase 2: Generate summaries for files that need them (parallel)
        files_to_process = code_scanner.files_needing_summary()
        if files_to_process:
            rprint(f"[cyan]→ Analyzing {len(files_to_process)} code changes...[/cyan]")
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task("Scanning", total=len(files_to_process))

                # Run with progress updates
                async def scan_with_progress():
                    state = code_scanner._load_state()
                    semaphore = asyncio.Semaphore(concurrency)

                    async def process_file(file_path: str):
                        async with semaphore:
                            state_item = state.get(file_path, {}).copy()
                            if not state_item.get("skipped") and not state_item.get("summary"):
                                updated = await code_scanner.describe_async(file_path, state_item)
                                state[file_path] = updated
                            progress.update(task, advance=1)

                    tasks = [process_file(fp) for fp in files_to_process]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    code_scanner._save_state(state)

                asyncio.run(scan_with_progress())
            rprint(f"[green]✓ Completed {len(files_to_process)} code analyses[/green]")
        else:
            rprint("[yellow]✓ All code changes already analyzed[/yellow]")
