"""Behavioral tests for subscribe(): the callback fires repeatedly, unsubscribe
stops the loop, request errors are delivered without stopping it, and a raising
callback surfaces from unsubscribe(). A fake transport with a call counter and a
low poll_interval drives the loop deterministically.

No JS golden output exists for subscribe (the JS suite only asserts baseRequestId
passing), so these assert observable behavior via a boundary transport double.
"""

import asyncio
import json
import time

import pytest

from cubejs_client import AsyncCubeClient, CubeClient, ResultSet
from cubejs_client.errors import RequestError
from cubejs_client.transport.base import RawResponse

LOAD_BODY = json.dumps(
    {
        "queryType": "regularQuery",
        "results": [
            {
                "query": {"measures": ["Orders.count"]},
                "data": [{"Orders.count": "5"}],
                "annotation": {
                    "measures": {"Orders.count": {"title": "Count", "shortTitle": "Count", "type": "number"}},
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {},
                },
            }
        ],
        "pivotQuery": {"measures": ["Orders.count"], "queryType": "regularQuery"},
    }
)


class _CountingTransport:
    authorization = None

    def __init__(self, text, status=200):
        self._text = text
        self._status = status
        self.count = 0

    def request(self, method, params):
        self.count += 1
        return RawResponse(status=self._status, text=self._text)


class _AsyncCountingTransport:
    authorization = None

    def __init__(self, text, status=200):
        self._text = text
        self._status = status
        self.count = 0

    async def request(self, method, params):
        self.count += 1
        return RawResponse(status=self._status, text=self._text)


def _wait_until(pred, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.005)
    return False


async def _await_until(pred, timeout=2.0):
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if pred():
            return True
        await asyncio.sleep(0.005)
    return False


def test_subscribe_invokes_callback_repeatedly_then_unsubscribe_stops():
    transport = _CountingTransport(LOAD_BODY)
    client = CubeClient(transport=transport, api_url="http://x", poll_interval=0.01)
    received = []

    sub = client.subscribe({"measures": ["Orders.count"]}, lambda err, rs: received.append((err, rs)))

    assert _wait_until(lambda: len(received) >= 2)
    sub.unsubscribe()
    stable = len(received)
    time.sleep(0.05)

    assert len(received) == stable  # no further callbacks after unsubscribe
    err, rs = received[0]
    assert err is None
    assert isinstance(rs, ResultSet)
    assert rs.raw_data() == [{"Orders.count": "5"}]


def test_subscribe_delivers_request_error_and_keeps_polling():
    transport = _CountingTransport('{"error": "Internal Server Error"}', status=500)
    client = CubeClient(transport=transport, api_url="http://x", poll_interval=0.01)
    received = []

    sub = client.subscribe({"measures": ["Orders.count"]}, lambda err, rs: received.append((err, rs)))

    assert _wait_until(lambda: len(received) >= 2)
    sub.unsubscribe()

    assert all(isinstance(err, RequestError) and rs is None for err, rs in received)


def test_subscribe_surfaces_callback_exception_from_unsubscribe():
    transport = _CountingTransport(LOAD_BODY)
    client = CubeClient(transport=transport, api_url="http://x", poll_interval=0.01)

    def cb(err, rs):
        raise ValueError("callback boom")

    sub = client.subscribe({"measures": ["Orders.count"]}, cb)

    assert _wait_until(lambda: sub.exception is not None)
    with pytest.raises(ValueError, match="callback boom"):
        sub.unsubscribe()


def test_sync_unsubscribe_returns_promptly_despite_large_poll_interval():
    # poll_interval is 5s, but the inter-cycle wait is interruptible, so
    # unsubscribe() must not block for the remainder of the interval.
    transport = _CountingTransport(LOAD_BODY)
    client = CubeClient(transport=transport, api_url="http://x", poll_interval=5.0)
    received = []

    sub = client.subscribe({"measures": ["Orders.count"]}, lambda err, rs: received.append((err, rs)))

    assert _wait_until(lambda: len(received) >= 1)
    start = time.time()
    sub.unsubscribe()
    assert time.time() - start < 1.0


async def test_subscribe_async_invokes_callback_then_unsubscribe_stops():
    transport = _AsyncCountingTransport(LOAD_BODY)
    client = AsyncCubeClient(transport=transport, api_url="http://x", poll_interval=0.01)
    received = []

    sub = client.subscribe({"measures": ["Orders.count"]}, lambda err, rs: received.append((err, rs)))

    assert await _await_until(lambda: len(received) >= 2)
    await sub.unsubscribe()
    stable = len(received)
    await asyncio.sleep(0.05)

    assert len(received) == stable
    assert received[0][0] is None
    assert isinstance(received[0][1], ResultSet)


async def test_subscribe_async_supports_async_callback():
    transport = _AsyncCountingTransport(LOAD_BODY)
    client = AsyncCubeClient(transport=transport, api_url="http://x", poll_interval=0.01)
    received = []

    async def cb(err, rs):
        received.append((err, rs))

    sub = client.subscribe({"measures": ["Orders.count"]}, cb)

    assert await _await_until(lambda: len(received) >= 2)
    await sub.unsubscribe()

    assert received[0][0] is None
    assert isinstance(received[0][1], ResultSet)


async def test_subscribe_async_surfaces_callback_exception_from_unsubscribe():
    transport = _AsyncCountingTransport(LOAD_BODY)
    client = AsyncCubeClient(transport=transport, api_url="http://x", poll_interval=0.01)

    def cb(err, rs):
        raise ValueError("async callback boom")

    sub = client.subscribe({"measures": ["Orders.count"]}, cb)

    assert await _await_until(lambda: sub.exception is not None)
    with pytest.raises(ValueError, match="async callback boom"):
        await sub.unsubscribe()
