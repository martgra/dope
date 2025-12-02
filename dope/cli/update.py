"""All-in-one command to update documentation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TaskProgressColumn, TextColumn

from dope.cli.apply import _apply_change
from dope.cli.common import command_context, get_branch_option
from dope.cli.suggest import _load_scope
from dope.core.progress import track

app = typer.Typer(
    epilog="""
Examples:
  # Run full workflow: scan → suggest → apply
  $ dope update

  # Preview changes without applying
  $ dope update --dry-run

  # Update using specific branch
  $ dope update --branch develop

  # Preview with higher concurrency
  $ dope update --dry-run --concurrency 10
    """
)

DEFAULT_CONCURRENCY = 5


@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show suggestions without applying changes"),
    ] = False,
    branch: get_branch_option() = None,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", help="Max parallel LLM calls")
    ] = DEFAULT_CONCURRENCY,
):
    """Update documentation: scan docs → scan code → suggest → apply (all-in-one)."""
    if ctx.resilient_parsing:
        return

    with command_context(branch=branch) as cmd_ctx:
        root_path = Path(".")

        # Phase 1: Scan documentation
        rprint("[cyan]→ Scanning documentation...[/cyan]")
        doc_scanner = cmd_ctx.factory.doc_scanner(root_path, cmd_ctx.tracker)
        doc_scanner.scan()

        files_to_process = doc_scanner.files_needing_summary()
        if files_to_process:
            rprint(f"  Processing {len(files_to_process)} files...")
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task("Scanning", total=len(files_to_process))

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

        doc_scanner.build_term_index()
        rprint("[green]✓ Documentation scan complete[/green]")

        # Phase 2: Scan code
        rprint(f"[cyan]→ Scanning code changes (branch: {cmd_ctx.branch})...[/cyan]")
        code_scanner = cmd_ctx.factory.code_scanner(root_path, cmd_ctx.branch, cmd_ctx.tracker)
        code_scanner.scan()

        files_to_process = code_scanner.files_needing_summary()
        if files_to_process:
            rprint(f"  Processing {len(files_to_process)} code changes...")
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task("Scanning", total=len(files_to_process))

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
        rprint("[green]✓ Code scan complete[/green]")

        # Phase 3: Generate suggestions
        rprint("[cyan]→ Generating suggestions...[/cyan]")
        suggester = cmd_ctx.factory.suggester(cmd_ctx.tracker)
        doc_state = doc_scanner.get_state()
        code_state = code_scanner.get_state()
        scope = _load_scope(cmd_ctx.settings)

        rprint("→ Generating suggestions...")
        suggester.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
        rprint("[green]✓ Suggestions generated[/green]")

        # Phase 4: Apply or display
        suggest_state = suggester.get_state()

        if dry_run:
            rprint("\n[yellow]Dry run - showing suggestions without applying:[/yellow]")
            for change in suggest_state.changes_to_apply:
                rprint(f"  • {change.documentation_file_path} ({change.change_type})")
                if change.suggested_changes:
                    for suggestion in change.suggested_changes[:2]:  # Show first 2
                        text = suggestion.suggestion
                        preview = text[:80] if len(text) > 80 else text
                        rprint(f"    - {preview}...")
            rprint(f"\n[yellow]Total changes: {len(suggest_state.changes_to_apply)}[/yellow]")
            rprint("[yellow]Run without --dry-run to apply changes[/yellow]")
        else:
            rprint("[cyan]→ Applying changes...[/cyan]")
            docs_changer = cmd_ctx.factory.docs_changer(root_path, cmd_ctx.branch, cmd_ctx.tracker)

            for suggested_change in track(
                suggest_state.changes_to_apply, description="Applying documentation changes"
            ):
                path, content = docs_changer.apply_suggestion(suggested_change)
                _apply_change(path, content)

            rprint("[green]✓ All changes applied successfully![/green]")
