"""Wiring tests for cube_sql_stream(): client -> transport.request_stream ->
chunk parser. A fake transport supplies canned byte chunks (deterministic); a
respx test covers the real HttpTransport streaming path end-to-end.
"""

import json

import httpx
import pytest
import respx

from cubejs_client import AsyncCubeClient, CubeClient

SCHEMA_LINE = json.dumps({"schema": [{"name": "status", "column_type": "String"}]})
DATA_LINE = json.dumps({"data": [["Cancelled"]]})


class _FakeStreamTransport:
    authorization = None

    def __init__(self, byte_chunks):
        self._byte_chunks = byte_chunks
        self.calls = []

    def request_stream(self, api_method, *, params, http_method="POST", fetch_timeout=None, base_request_id=None):
        self.calls.append({"api_method": api_method, "params": dict(params), "http_method": http_method})
        return iter(self._byte_chunks)


class _FakeAsyncStreamTransport:
    authorization = None

    def __init__(self, byte_chunks):
        self._byte_chunks = byte_chunks
        self.calls = []

    def request_stream(self, api_method, *, params, http_method="POST", fetch_timeout=None, base_request_id=None):
        self.calls.append({"api_method": api_method, "params": dict(params)})

        async def _gen():
            for c in self._byte_chunks:
                yield c

        return _gen()


class _NoStreamTransport:
    authorization = None

    def request(self, method, params):  # pragma: no cover - never reached
        raise AssertionError("should not be called")


def test_cube_sql_stream_yields_typed_chunks_and_passes_query():
    fake = _FakeStreamTransport([f"{SCHEMA_LINE}\n".encode(), f"{DATA_LINE}\n".encode()])
    client = CubeClient(transport=fake, api_url="http://x")

    chunks = list(client.cube_sql_stream("SELECT status FROM orders"))

    assert chunks == [
        {"type": "schema", "schema": [{"name": "status", "column_type": "String"}]},
        {"type": "data", "data": [["Cancelled"]]},
    ]
    assert fake.calls[0]["api_method"] == "cubesql"
    assert fake.calls[0]["params"]["query"] == "SELECT status FROM orders"
    assert fake.calls[0]["http_method"] == "POST"


async def test_cube_sql_stream_async_yields_typed_chunks():
    fake = _FakeAsyncStreamTransport([f"{SCHEMA_LINE}\n{DATA_LINE}\n".encode()])
    client = AsyncCubeClient(transport=fake, api_url="http://x")

    chunks = [c async for c in client.cube_sql_stream("SELECT status FROM orders")]

    assert chunks == [
        {"type": "schema", "schema": [{"name": "status", "column_type": "String"}]},
        {"type": "data", "data": [["Cancelled"]]},
    ]


def test_cube_sql_stream_raises_without_transport_support():
    client = CubeClient(transport=_NoStreamTransport(), api_url="http://x")
    with pytest.raises(RuntimeError, match="does not support streaming"):
        list(client.cube_sql_stream("SELECT 1"))


@respx.mock
def test_cube_sql_stream_over_real_http_transport():
    payload = f"{SCHEMA_LINE}\n{DATA_LINE}\n".encode()
    route = respx.post("http://localhost:4000/cubejs-api/v1/cubesql").mock(
        return_value=httpx.Response(200, content=payload)
    )

    client = CubeClient("token", api_url="http://localhost:4000/cubejs-api/v1")
    chunks = list(client.cube_sql_stream("SELECT status FROM orders"))

    assert {"type": "schema", "schema": [{"name": "status", "column_type": "String"}]} in chunks
    assert {"type": "data", "data": [["Cancelled"]]} in chunks
    sent = json.loads(route.calls[0].request.content)
    assert sent["query"] == "SELECT status FROM orders"
