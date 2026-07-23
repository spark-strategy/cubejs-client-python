"""Handles returned by `CubeClient.subscribe` / `AsyncCubeClient.subscribe`.

These replace JS's `UnsubscribeObj` (index.ts:87-93). Cancellation is native:
the sync `Subscription` runs the poll loop on a daemon thread stopped via a
`threading.Event`; the `AsyncSubscription` runs it as an `asyncio.Task` that is
cancelled. If the caller's callback raises, the loop stops and the exception is
re-raised from `unsubscribe()` (and available as `.exception`).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Optional


class Subscription:
    """Sync subscription handle. Call `unsubscribe()` to stop polling."""

    def __init__(self, thread: threading.Thread, stop_event: threading.Event):
        self._thread = thread
        self._stop_event = stop_event
        self.exception: Optional[BaseException] = None

    def unsubscribe(self, timeout: Optional[float] = None) -> None:
        """Stop the poll loop and wait for the worker thread to finish. Re-raises
        any exception a callback raised inside the loop."""
        self._stop_event.set()
        self._thread.join(timeout)
        if self.exception is not None:
            raise self.exception


class AsyncSubscription:
    """Async subscription handle. `await unsubscribe()` to stop polling."""

    def __init__(self, task: "asyncio.Task", stop_event: asyncio.Event):
        self._task = task
        self._stop_event = stop_event
        self.exception: Optional[BaseException] = None

    async def unsubscribe(self) -> None:
        """Stop the poll loop and await the task's completion. Re-raises any
        exception a callback raised inside the loop."""
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        if self.exception is not None:
            raise self.exception
