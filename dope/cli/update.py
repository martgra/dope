"""All-in-one command to update documentation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from dope.cli.apply import _apply_change
from dope.cli.common import command_context, get_branch_option
from dope.cli.suggest import _load_scope
from dope.cli.ui import ProgressReporter, StatusFormatter, info, success
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
        info("Scanning documentation...")
        doc_scanner = cmd_ctx.factory.doc_scanner(root_path, cmd_ctx.tracker)
        doc_scanner.scan()

        files_to_process = doc_scanner.files_needing_summary()
        if files_to_process:
            info(f"Processing {len(files_to_process)} files...")
            scan_with_progress = ProgressReporter.create_async_scanner(
                doc_scanner, files_to_process, "Scanning", concurrency
            )
            asyncio.run(scan_with_progress())

        doc_scanner.build_term_index()
        success("Documentation scan complete")

        # Phase 2: Scan code
        info(f"Scanning code changes (branch: {cmd_ctx.branch})...")
        code_scanner = cmd_ctx.factory.code_scanner(root_path, cmd_ctx.branch, cmd_ctx.tracker)
        code_scanner.scan()

        files_to_process = code_scanner.files_needing_summary()
        if files_to_process:
            info(f"Processing {len(files_to_process)} code changes...")
            scan_with_progress = ProgressReporter.create_async_scanner(
                code_scanner, files_to_process, "Scanning", concurrency
            )
            asyncio.run(scan_with_progress())
        success("Code scan complete")

        # Phase 3: Generate suggestions
        info("Generating suggestions...")
        suggester = cmd_ctx.factory.suggester(cmd_ctx.tracker)
        doc_state = doc_scanner.get_state()
        code_state = code_scanner.get_state()
        scope = _load_scope(cmd_ctx.settings)

        suggester.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
        success("Suggestions generated")

        # Phase 4: Apply or display
        suggest_state = suggester.get_state()

        if dry_run:
            StatusFormatter.display_dry_run_preview(suggest_state.changes_to_apply)
        else:
            info("Applying changes...")
            docs_changer = cmd_ctx.factory.docs_changer(root_path, cmd_ctx.branch, cmd_ctx.tracker)

            for suggested_change in track(
                suggest_state.changes_to_apply, description="Applying documentation changes"
            ):
                path, content = docs_changer.apply_suggestion(suggested_change)
                _apply_change(path, content)

            success("All changes applied successfully!")
