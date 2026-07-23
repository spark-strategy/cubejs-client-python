"""Port of CubeApi.loadMethod's polling/retry state machine (src/index.ts:294-437),
restructured around a plain retry loop that calls `request_fn` again for each
attempt, rather than JS's closure/subscribe re-invocation (see
transport.base for why). `subscribe()`'s continuous long-poll and the mutex
machinery are deferred to a later phase; this covers single-shot
load/meta/sql/dry-run with Continue-wait and network-error retries.
"""

from __future__ import annotations

import json
import time as time_module
from typing import Any, Callable, Optional

from ..errors import RequestError
from ..models.progress import ProgressResult
from ..transport.base import RawResponse


def run_polling_loop(
    *,
    request_fn: Callable[[], RawResponse],
    to_result: Callable[[dict], Any],
    poll_interval: float = 5.0,
    network_error_retries: int = 0,
    progress_callback: Optional[Callable[[ProgressResult], None]] = None,
    sleep: Callable[[float], None] = time_module.sleep,
) -> Any:
    retries_left = network_error_retries

    while True:
        response = request_fn()

        is_bad_gateway = response.status == 502
        # Any transport-level failure (network error, timeout, aborted) counts
        # against the retry budget. The JS SDK only retries a literal
        # "network error" string and leaves timeouts to crash immediately
        # (index.ts:363-390); that's a bug there, not a contract worth
        # reproducing, so this is deliberately broader.
        is_transport_error = response.error is not None

        if is_bad_gateway or is_transport_error:
            should_retry = is_bad_gateway
            if is_transport_error and not is_bad_gateway:
                retries_left -= 1
                should_retry = retries_left >= 0
            if should_retry:
                sleep(poll_interval)
                continue

        if response.error is not None and response.status is None:
            # Transport-level failure (timeout/aborted, or a network error with
            # retries exhausted) never produced an HTTP response to parse.
            raise RequestError(response.error, {"error": response.error}, 0)

        text = response.text or ""
        try:
            body = json.loads(text)
            if not isinstance(body, dict):
                body = {"error": text}
        except ValueError:
            body = {"error": text}

        if body.get("error") and "Continue wait" in body["error"]:
            if progress_callback:
                progress_callback(ProgressResult(body))
            sleep(poll_interval)
            continue

        if response.status != 200:
            raise RequestError(body.get("error") or "", body, response.status or 0)

        return to_result(body)
