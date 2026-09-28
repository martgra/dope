"""Cache decorator scoped to the currently running event loop.

Regular :func:`functools.lru_cache` holds one entry per argument tuple across
the process lifetime. This variant additionally invalidates entries when the
running event loop changes, which is required for anything that constructs,
holds, or transitively references an :class:`httpx.AsyncClient` — that
client's transport binds to whichever loop first touches it, so reusing it
across loop boundaries raises ``RuntimeError: Event loop is closed``.

Loops are keyed by object identity (via :class:`weakref.WeakKeyDictionary`)
rather than by ``id()``, because the CPython allocator may reuse a freed
loop's ``id`` for a subsequent one — that would silently keep serving the
stale entry.

Fall-back cache when no loop is running is a plain dict, so pure-sync callers
still get memoization; if a subsequent async call opens a fresh loop, that
loop gets its own entry.
"""

from __future__ import annotations

import asyncio
import functools
import weakref
from collections.abc import Callable
from typing import Any, cast


def loop_scoped_cache[F: Callable[..., Any]](func: F) -> F:
    """Memoize ``func`` by ``(loop, *args)``, rebuilding on loop change.

    Attaches ``cache_clear()`` for parity with :func:`functools.lru_cache`.
    """
    per_loop: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
    sync_cache: dict[tuple, Any] = {}

    @functools.wraps(func)
    def wrapper(*args: Any) -> Any:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        cache = sync_cache if loop is None else per_loop.setdefault(loop, {})
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    def cache_clear() -> None:
        per_loop.clear()
        sync_cache.clear()

    wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
    return cast(F, wrapper)
