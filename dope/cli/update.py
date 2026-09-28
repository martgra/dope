"""All-in-one command to update documentation."""

import asyncio
from typing import Annotated

import typer

from dope.cli.apply import apply_suggestions
from dope.cli.common import command_context
from dope.cli.ui import ProgressReporter, StatusFormatter, info, success

app = typer.Typer(
    epilog="""
Examples:
    # Preview the full workflow
  $ dope update

    # Apply generated changes
    $ dope update --apply

  # Update using specific branch
  $ dope update --branch develop

    # Preview with higher concurrency
    $ dope update --concurrency 10
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
    apply_changes: Annotated[
        bool,
        typer.Option("--apply", help="Apply suggestions after showing the workflow result"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview suggestions without applying changes (default)"),
    ] = False,
    branch: Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to compare against (defaults to configured branch)",
        ),
    ] = None,
    concurrency: Annotated[
        int, typer.Option("--concurrency", "-c", min=1, help="Max parallel LLM calls")
    ] = DEFAULT_CONCURRENCY,
):
    """Scan docs and code, then preview suggestions or apply them with --apply."""
    if ctx.resilient_parsing:
        return
    if dry_run and apply_changes:
        raise typer.BadParameter("--dry-run cannot be used with --apply")

    with command_context(branch=branch) as cmd_ctx:
        # Phase 1: Scan documentation
        info("Scanning documentation...")
        doc_scanner = cmd_ctx.factory.doc_scanner(cmd_ctx.docs_root, cmd_ctx.tracker)
        doc_scanner.scan()
        _process_pending_files(doc_scanner, "files", concurrency)
        doc_scanner.build_term_index()
        success("Documentation scan complete")

        # Phase 2: Scan code
        info(f"Scanning code changes (branch: {cmd_ctx.branch})...")
        code_scanner = cmd_ctx.factory.code_scanner(
            cmd_ctx.code_root, cmd_ctx.branch, cmd_ctx.tracker
        )
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

        if dry_run or not apply_changes:
            StatusFormatter.display_dry_run_preview(suggest_state.changes_to_apply)
        else:
            info("Applying changes...")
            docs_changer = cmd_ctx.factory.docs_changer(
                cmd_ctx.docs_root, cmd_ctx.code_root, cmd_ctx.branch, cmd_ctx.tracker
            )

            applied_count = apply_suggestions(docs_changer, suggest_state.changes_to_apply)
            success(f"Applied {applied_count} documentation suggestions.")
