"""Golden tests for CubeSQL response parsing, transcribed verbatim from the JS
SDK's test/CubeApi.test.ts ('CubeApi cubeSql' describe block, lines 403-507).

The JS backend streams JSON Lines *inside* the response body's `error` field
(a documented quirk — both errors and successful results arrive as `error`).
`parse_cubesql_response` receives the already-JSON-parsed body dict (the shape
the polling loop hands to `to_result`) and flattens the JSONL into
`{schema, data, lastRefreshTime?}`.
"""

import json

import pytest

from cubejs_client.core.cubesql import parse_cubesql_response


def _jsonl_body(*chunks: dict) -> dict:
    """Mirror the JS fixtures: JSON.stringify each chunk, join with '\\n', wrap
    in `{error: ...}` — the body shape the transport delivers."""
    return {"error": "\n".join(json.dumps(c) for c in chunks)}


def test_parses_last_refresh_time_and_flattens_data():
    body = _jsonl_body(
        {
            "schema": [
                {"name": "status", "column_type": "String"},
                {"name": "measure(orders_transactions.count)", "column_type": "Int64"},
            ],
            "lastRefreshTime": "2026-02-24T00:34:01.594Z",
        },
        {"data": [["Cancelled", "27090"], ["Returned", "18232"]]},
        {"data": [["Shipped", "45102"]]},
    )

    res = parse_cubesql_response(body)

    assert res["lastRefreshTime"] == "2026-02-24T00:34:01.594Z"
    assert res["schema"] == [
        {"name": "status", "column_type": "String"},
        {"name": "measure(orders_transactions.count)", "column_type": "Int64"},
    ]
    assert res["data"] == [
        ["Cancelled", "27090"],
        ["Returned", "18232"],
        ["Shipped", "45102"],
    ]


def test_omits_last_refresh_time_when_absent():
    body = _jsonl_body(
        {"schema": [{"name": "status", "column_type": "String"}]},
        {"data": [["Active"]]},
    )

    res = parse_cubesql_response(body)

    assert "lastRefreshTime" not in res
    assert res["schema"] == [{"name": "status", "column_type": "String"}]
    assert res["data"] == [["Active"]]


def test_surfaces_error_chunk_following_the_schema():
    body = _jsonl_body(
        {"schema": [{"name": "created_date", "column_type": "String"}]},
        {
            "error": "Post-Processing Error: Cast error: Error parsing '2026-05-01' as timestamp",
            "requestId": "2fbe44e4-df6f-420d-ae39-376c802323b4-span-1",
        },
    )

    with pytest.raises(Exception) as exc_info:
        parse_cubesql_response(body)

    assert "Post-Processing Error: Cast error: Error parsing '2026-05-01' as timestamp" in str(exc_info.value)
