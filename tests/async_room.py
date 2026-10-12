"""Bounded observation of async room behavior, without invoking worker internals."""

import asyncio


async def wait_until(predicate, *, timeout=2):
    """Wait for an observable state/event; fail rather than hanging a fixture."""
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(.001)
