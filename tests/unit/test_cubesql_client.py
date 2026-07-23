"""End-to-end wiring for cube_sql(): client -> HttpTransport (POST /cubesql) ->
polling loop -> parse_cubesql_response, against a mocked HTTP server.

The backend delivers JSONL inside the body's `error` field (see
test_cubesql_golden.py); here we verify the client returns the flattened result
and issues a POST carrying the SQL string.
"""

import json

import httpx
import pytest
import respx

from cubejs_client import AsyncCubeClient, cube


def _cubesql_body() -> dict:
    return {
        "error": "\n".join(
            json.dumps(c)
            for c in (
                {
                    "schema": [{"name": "status", "column_type": "String"}],
                    "lastRefreshTime": "2026-02-24T00:34:01.594Z",
                },
                {"data": [["Cancelled"], ["Shipped"]]},
            )
        )
    }


@respx.mock
def test_cube_sql_returns_flattened_result_and_posts_sql():
    route = respx.post("http://localhost:4000/cubejs-api/v1/cubesql").mock(
        return_value=httpx.Response(200, json=_cubesql_body())
    )

    client = cube("token", api_url="http://localhost:4000/cubejs-api/v1")
    res = client.cube_sql("SELECT status FROM orders_transactions")

    assert res["schema"] == [{"name": "status", "column_type": "String"}]
    assert res["data"] == [["Cancelled"], ["Shipped"]]
    assert res["lastRefreshTime"] == "2026-02-24T00:34:01.594Z"

    sent = json.loads(route.calls[0].request.content)
    assert sent["query"] == "SELECT status FROM orders_transactions"


@respx.mock
async def test_cube_sql_async_returns_flattened_result():
    respx.post("http://localhost:4000/cubejs-api/v1/cubesql").mock(
        return_value=httpx.Response(200, json=_cubesql_body())
    )

    client = AsyncCubeClient("token", api_url="http://localhost:4000/cubejs-api/v1")
    res = await client.cube_sql("SELECT status FROM orders_transactions")

    assert res["data"] == [["Cancelled"], ["Shipped"]]
    assert res["lastRefreshTime"] == "2026-02-24T00:34:01.594Z"


@respx.mock
def test_cube_sql_surfaces_error_chunk():
    body = {
        "error": "\n".join(
            json.dumps(c)
            for c in (
                {"schema": [{"name": "created_date", "column_type": "String"}]},
                {"error": "Post-Processing Error: bad cast"},
            )
        )
    }
    respx.post("http://localhost:4000/cubejs-api/v1/cubesql").mock(
        return_value=httpx.Response(200, json=body)
    )

    client = cube("token", api_url="http://localhost:4000/cubejs-api/v1")
    with pytest.raises(Exception) as exc_info:
        client.cube_sql("SELECT created_date FROM deals")

    assert "Post-Processing Error: bad cast" in str(exc_info.value)
