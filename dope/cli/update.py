"""All-in-one command to update documentation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from dope.cli.apply import _apply_change
from dope.cli.common import BranchOption, command_context
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


def _process_pending_files(scanner, work_description: str, concurrency: int) -> None:
    """Process scanner files that need summaries with progress reporting."""
    files_to_process = scanner.files_needing_summary()
    if not files_to_process:
        return

    info(f"Processing {len(files_to_process)} {work_description}...")
    scan_with_progress = ProgressReporter.create_async_scanner(
        scanner, files_to_process, "Scanning", concurrency
    )
    asyncio.run(scan_with_progress())


@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show suggestions without applying changes"),
    ] = False,
    branch: BranchOption = None,
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
        _process_pending_files(doc_scanner, "files", concurrency)
        doc_scanner.build_term_index()
        success("Documentation scan complete")

        # Phase 2: Scan code
        info(f"Scanning code changes (branch: {cmd_ctx.branch})...")
        code_scanner = cmd_ctx.factory.code_scanner(root_path, cmd_ctx.branch, cmd_ctx.tracker)
        code_scanner.scan()
        _process_pending_files(code_scanner, "code changes", concurrency)
        success("Code scan complete")

        # Phase 3: Generate suggestions
        info("Generating suggestions...")
        suggester = cmd_ctx.factory.suggester(cmd_ctx.tracker)
        doc_state = doc_scanner.get_state()
        code_state = code_scanner.get_state()

        suggester.get_suggestions(docs_change=doc_state, code_change=code_state)
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
