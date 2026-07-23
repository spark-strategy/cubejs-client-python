"""Port of CubeApi.loadMethod's polling/retry state machine (src/index.ts:294-437),
restructured around a plain retry loop that calls `request_fn` again for each
attempt, rather than JS's closure/subscribe re-invocation (see
transport.base for why). This covers single-shot load/meta/sql/dry-run with
Continue-wait and network-error retries.

`run_subscribe_loop` layers `subscribe()`'s continuous long-poll on top: it
re-runs a single-shot poll, invokes the caller's callback with each result (or
error), then sleeps `poll_interval` and repeats until a stop predicate flips —
the degraded HTTP-polling form of JS's `subscribeNext` (index.ts:335-345),
since this port's transport has no push/`unsubscribe`. Cancellation is native
(a threading.Event / task cancellation supplied by the client); JS's
`mutexObj`/`mutexKey` supersession is deliberately not ported.

Each `run_*_async` is the same state machine with `await`s, for
`AsyncCubeClient`. Keep the pairs in lockstep by hand — see the sync versions'
docstrings for the semantics both share.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import time as time_module
from typing import Any, Awaitable, Callable, Optional, Union

from ..errors import RequestError
from ..models.progress import ProgressResult
from ..transport.base import RawResponse

SubscribeCallback = Callable[[Optional[RequestError], Any], Any]


class _SubscriptionStopped(Exception):
    """Internal sentinel: `should_stop()` flipped mid-poll (e.g. `unsubscribe()`
    during a Continue-wait retry). Caught by the subscribe loops to exit cleanly;
    never escapes to callers."""


def run_polling_loop(
    *,
    request_fn: Callable[[], RawResponse],
    to_result: Callable[[dict], Any],
    poll_interval: float = 5.0,
    network_error_retries: int = 0,
    progress_callback: Optional[Callable[[ProgressResult], None]] = None,
    sleep: Callable[[float], None] = time_module.sleep,
    should_stop: Callable[[], bool] = lambda: False,
) -> Any:
    retries_left = network_error_retries

    while True:
        if should_stop():
            raise _SubscriptionStopped
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


async def run_polling_loop_async(
    *,
    request_fn: Callable[[], Awaitable[RawResponse]],
    to_result: Callable[[dict], Any],
    poll_interval: float = 5.0,
    network_error_retries: int = 0,
    progress_callback: Optional[Callable[[ProgressResult], Union[None, Awaitable[None]]]] = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    should_stop: Callable[[], bool] = lambda: False,
) -> Any:
    retries_left = network_error_retries

    while True:
        if should_stop():
            raise _SubscriptionStopped
        response = await request_fn()

        is_bad_gateway = response.status == 502
        is_transport_error = response.error is not None

        if is_bad_gateway or is_transport_error:
            should_retry = is_bad_gateway
            if is_transport_error and not is_bad_gateway:
                retries_left -= 1
                should_retry = retries_left >= 0
            if should_retry:
                await sleep(poll_interval)
                continue

        if response.error is not None and response.status is None:
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
                maybe_awaitable = progress_callback(ProgressResult(body))
                if inspect.isawaitable(maybe_awaitable):
                    await maybe_awaitable
            await sleep(poll_interval)
            continue

        if response.status != 200:
            raise RequestError(body.get("error") or "", body, response.status or 0)

        return to_result(body)


def run_subscribe_loop(
    *,
    request_fn: Callable[[], RawResponse],
    to_result: Callable[[dict], Any],
    callback: SubscribeCallback,
    should_stop: Callable[[], bool],
    poll_interval: float = 5.0,
    network_error_retries: int = 0,
    update_authorization: Callable[[], None] = lambda: None,
    sleep: Callable[[float], None] = time_module.sleep,
) -> None:
    """Continuous long-poll: run one single-shot poll per cycle, hand the result
    (or a `RequestError`) to `callback`, sleep `poll_interval`, repeat until
    `should_stop()`. Errors do not stop the loop — matching JS, which calls
    `subscribeNext()` after an error too (index.ts:403)."""
    while not should_stop():
        update_authorization()
        try:
            result = run_polling_loop(
                request_fn=request_fn,
                to_result=to_result,
                poll_interval=poll_interval,
                network_error_retries=network_error_retries,
                sleep=sleep,
                should_stop=should_stop,
            )
        except _SubscriptionStopped:
            break
        except RequestError as error:
            callback(error, None)
        else:
            if should_stop():
                break
            callback(None, result)
        if should_stop():
            break
        sleep(poll_interval)


async def run_subscribe_loop_async(
    *,
    request_fn: Callable[[], Awaitable[RawResponse]],
    to_result: Callable[[dict], Any],
    callback: SubscribeCallback,
    should_stop: Callable[[], bool],
    poll_interval: float = 5.0,
    network_error_retries: int = 0,
    update_authorization: Callable[[], None] = lambda: None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Async twin of `run_subscribe_loop`. The callback may be sync or async."""
    while not should_stop():
        update_authorization()
        try:
            result = await run_polling_loop_async(
                request_fn=request_fn,
                to_result=to_result,
                poll_interval=poll_interval,
                network_error_retries=network_error_retries,
                sleep=sleep,
                should_stop=should_stop,
            )
        except _SubscriptionStopped:
            break
        except RequestError as error:
            maybe = callback(error, None)
            if inspect.isawaitable(maybe):
                await maybe
        else:
            if should_stop():
                break
            maybe = callback(None, result)
            if inspect.isawaitable(maybe):
                await maybe
        if should_stop():
            break
        await sleep(poll_interval)
