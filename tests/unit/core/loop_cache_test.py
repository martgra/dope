"""Unit tests for dope.core.loop_cache."""

import asyncio

from dope.core.loop_cache import loop_scoped_cache


def test_loop_scoped_cache_memoizes_within_a_loop():
    """Same-loop repeat calls return the cached value."""
    counter = {"n": 0}

    @loop_scoped_cache
    def factory():
        counter["n"] += 1
        return object()

    async def run():
        return factory(), factory(), factory()

    a, b, c = asyncio.run(run())
    assert a is b is c
    assert counter["n"] == 1


def test_loop_scoped_cache_rebuilds_across_loops():
    """A fresh event loop rebuilds the cached value."""
    counter = {"n": 0}

    @loop_scoped_cache
    def factory():
        counter["n"] += 1
        return object()

    async def run():
        return factory()

    first = asyncio.run(run())
    second = asyncio.run(run())
    assert first is not second
    assert counter["n"] == 2


def test_loop_scoped_cache_sync_context_shares_entry():
    """No running loop → all sync callers share the same entry."""
    counter = {"n": 0}

    @loop_scoped_cache
    def factory():
        counter["n"] += 1
        return object()

    a, b = factory(), factory()
    assert a is b
    assert counter["n"] == 1


def test_loop_scoped_cache_respects_args():
    """Different args produce different cache entries within one loop."""

    @loop_scoped_cache
    def factory(x):
        return (x, object())

    async def run():
        return factory("a"), factory("b"), factory("a")

    a1, b, a2 = asyncio.run(run())
    assert a1 == a2  # same key → same entry
    assert a1[1] is a2[1]
    assert a1[1] is not b[1]


def test_loop_scoped_cache_clear():
    """cache_clear resets the memoization."""
    counter = {"n": 0}

    @loop_scoped_cache
    def factory():
        counter["n"] += 1
        return object()

    factory()
    factory()
    assert counter["n"] == 1
    factory.cache_clear()
    factory()
    assert counter["n"] == 2
