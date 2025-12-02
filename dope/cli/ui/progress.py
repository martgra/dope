"""Progress tracking abstractions for CLI operations."""

import asyncio
from collections.abc import Callable, Iterable
from typing import Any

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)


class ProgressReporter:
    """Unified progress tracking for various CLI operations."""

    @staticmethod
    def track_iterable(items: Iterable[Any], description: str) -> Iterable[Any]:
        """Track progress through an iterable with a progress bar.

        Args:
            items: Iterable to track
            description: Description of the operation

        Yields:
            Items from the iterable
        """
        items_list = list(items)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
        ) as progress:
            task = progress.add_task(description, total=len(items_list))
            for item in items_list:
                yield item
                progress.update(task, advance=1)

    @staticmethod
    async def track_async(
        items: list[str],
        processor: Callable[[str], Any],
        description: str,
        concurrency: int = 5,
    ) -> None:
        """Track progress through async operations with concurrency control.

        Args:
            items: List of items to process
            processor: Async function to process each item
            description: Description of the operation
            concurrency: Maximum concurrent operations
        """
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
        ) as progress:
            task = progress.add_task(description, total=len(items))
            semaphore = asyncio.Semaphore(concurrency)

            async def process_with_semaphore(item: str) -> Any:
                async with semaphore:
                    result = await processor(item)
                    progress.update(task, advance=1)
                    return result

            tasks = [process_with_semaphore(item) for item in items]
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def spinner(description: str) -> Progress:
        """Create a spinner for indeterminate operations.

        Args:
            description: Description of the operation

        Returns:
            Progress context manager with spinner

        Example:
            with ProgressReporter.spinner("Processing...") as progress:
                progress.add_task(description="", total=None)
                # Do work
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        )

    @staticmethod
    def create_async_scanner(
        scanner: Any,
        files_to_process: list[str],
        description: str,
        concurrency: int,
    ) -> Callable:
        """Create async scanner function with progress tracking.

        Args:
            scanner: Scanner instance with describe_async method
            files_to_process: List of file paths to process
            description: Description for progress bar
            concurrency: Maximum concurrent operations

        Returns:
            Async function that processes files with progress tracking
        """

        async def scan_with_progress() -> None:
            """Process files with progress tracking and state management."""
            state = scanner._load_state()
            semaphore = asyncio.Semaphore(concurrency)

            async def process_file(file_path: str) -> None:
                async with semaphore:
                    state_item = state.get(file_path, {}).copy()
                    if not state_item.get("skipped") and not state_item.get("summary"):
                        updated = await scanner.describe_async(file_path, state_item)
                        state[file_path] = updated

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task(description, total=len(files_to_process))

                async def process_with_progress(file_path: str) -> None:
                    await process_file(file_path)
                    progress.update(task, advance=1)

                tasks = [process_with_progress(fp) for fp in files_to_process]
                await asyncio.gather(*tasks, return_exceptions=True)

            scanner._save_state(state)

        return scan_with_progress
