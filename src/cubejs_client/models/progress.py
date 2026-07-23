"""Port of ProgressResult.ts."""

from __future__ import annotations

from typing import Mapping


class ProgressResult:
    def __init__(self, progress_response: Mapping):
        self._progress_response = progress_response

    def stage(self) -> str:
        return self._progress_response["stage"]

    def time_elapsed(self) -> float:
        return self._progress_response["timeElapsed"]
