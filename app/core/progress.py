from collections.abc import Iterable, Iterator

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)


def track[T](
    iterable: Iterable[T],
    description: str = "Processing",
    total: int | None = None,
) -> Iterator[T]:
    """Track progressbar.

    Args:
    iterable (Iterable[T]): Any iterable
    description (str, optional): Description. Defaults to "Processing".
    total (int | None, optional): Total items. Defaults to len(Iterable).

    Yields:
    Iterator[T]: _description_
    """
    # try to infer total if not provided
    if total is None and hasattr(iterable, "__len__"):
        total = len(iterable)  # type: ignore
    columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),  # shows “37/100”
        TimeRemainingColumn(),  # ETA
    ]
    with Progress(*columns) as progress:
        task_id = progress.add_task(description, total=total)
        for item in iterable:
            yield item
            progress.advance(task_id)
