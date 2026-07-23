"""Port of RequestError.ts, plus the mutex-cancellation sentinel used internally
by the polling loop (CubeApi.loadMethod's `MUTEX_ERROR`)."""

from __future__ import annotations

from typing import Any


class CubeError(Exception):
    """Base class for errors raised by this SDK."""


class RequestError(CubeError):
    def __init__(self, message: str, response: Any, status: int):
        super().__init__(message)
        self.response = response
        self.status = status


class CubeSqlError(CubeError):
    """Raised when a CubeSQL query (`cube_sql`) returns an error payload — either
    a malformed response or an error chunk streamed after the schema line
    (mirrors the `Error` thrown by JS `cubeSql`'s result parser)."""


class MutexChangedError(CubeError):
    """Mirrors JS's `MUTEX_ERROR`, raised when a newer request with the same
    mutex key superseded an older one (index.ts:153).

    Intentionally unused in this port: JS needs the `mutexObj`/`mutexKey`
    shared-dict pattern because it has no cancellation primitive for
    fire-and-forget promises. `subscribe()` here instead uses native
    cancellation (a `threading.Event` for the sync client, task cancellation for
    the async one), so nothing raises this. Kept only so a caller that imported
    it against the JS error name still resolves.
    """
