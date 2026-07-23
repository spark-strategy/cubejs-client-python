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


class MutexChangedError(CubeError):
    """Raised internally when a newer request with the same mutex key superseded
    this one; callers should not normally see this (mirrors JS's MUTEX_ERROR).

    Currently unused: the mutex machinery only matters for `subscribe()`'s
    continuous long-poll, which is not implemented yet (deferred to a later
    phase). Kept as a stub so that phase's error contract is already in place.
    """
