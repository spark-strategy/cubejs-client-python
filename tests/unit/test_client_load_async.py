"""Async twin of test_client_load.py: AsyncCubeClient -> AsyncHttpTransport ->
async polling loop -> ResultSet, against a mocked HTTP server."""

import json

import httpx
import respx

from cubejs_client import AsyncCubeClient, Query, dim


@respx.mock
async def test_load_returns_result_set_usable_as_dataframe():
    respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(
            200,
            json={
                "queryType": "regularQuery",
                "results": [
                    {
                        "query": {"measures": ["Orders.count"], "dimensions": ["Orders.status"]},
                        "data": [
                            {"Orders.status": "completed", "Orders.count": "5"},
                            {"Orders.status": "shipped", "Orders.count": "3"},
                        ],
                        "annotation": {
                            "measures": {
                                "Orders.count": {"title": "Orders Count", "shortTitle": "Count", "type": "number"}
                            },
                            "dimensions": {
                                "Orders.status": {"title": "Orders Status", "shortTitle": "Status", "type": "string"}
                            },
                            "segments": {},
                            "timeDimensions": {},
                        },
                    }
                ],
                "pivotQuery": {
                    "measures": ["Orders.count"],
                    "dimensions": ["Orders.status"],
                    "queryType": "regularQuery",
                },
            },
        )
    )

    client = AsyncCubeClient(api_url="http://localhost:4000/cubejs-api/v1")
    result_set = await client.load(Query().measures("Orders.count").dimensions("Orders.status"))

    assert result_set.raw_data() == [
        {"Orders.status": "completed", "Orders.count": "5"},
        {"Orders.status": "shipped", "Orders.count": "3"},
    ]

    df = result_set.to_pandas()
    assert list(df["Orders.status"]) == ["completed", "shipped"]
    assert list(df["Orders.count"]) == [5, 3]


@respx.mock
async def test_load_accepts_plain_dict_query_and_dim_filter():
    route = respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(
            200,
            json={
                "queryType": "regularQuery",
                "results": [
                    {
                        "query": {"measures": ["Orders.count"]},
                        "data": [{"Orders.count": "1"}],
                        "annotation": {
                            "measures": {"Orders.count": {"title": "Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {},
                            "segments": {},
                            "timeDimensions": {},
                        },
                    }
                ],
                "pivotQuery": {"measures": ["Orders.count"], "queryType": "regularQuery"},
            },
        )
    )

    client = AsyncCubeClient(api_url="http://localhost:4000/cubejs-api/v1")
    result_set = await client.load(
        {"measures": ["Orders.count"], "filters": [dim("Orders.status") == "completed"]}
    )

    assert result_set.total_rows() is None
    sent_query = json.loads(route.calls[0].request.url.params["query"])
    assert sent_query["filters"] == [
        {"member": "Orders.status", "operator": "equals", "values": ["completed"]}
    ]
