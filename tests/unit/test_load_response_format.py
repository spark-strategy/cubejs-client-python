"""load(response_format=...) opt-in: requesting 'compact'/'columnar' stamps
`responseFormat` onto the outgoing query (patchQueryInternal parity); the
default leaves the query untouched.
"""

import json

import httpx
import respx

from cubejs_client import AsyncCubeClient, cube
from cubejs_client.query.model import patch_query_response_format

_OK_RESPONSE = {
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
}


def test_patch_helper_stamps_and_skips():
    assert patch_query_response_format({"measures": ["m"]}, "compact") == {
        "measures": ["m"],
        "responseFormat": "compact",
    }
    assert patch_query_response_format({"measures": ["m"]}, "default") == {"measures": ["m"]}
    # already the requested format -> unchanged (no new dict content)
    assert patch_query_response_format({"responseFormat": "columnar"}, "columnar") == {"responseFormat": "columnar"}


@respx.mock
def test_load_compact_sets_response_format_on_query():
    route = respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(200, json=_OK_RESPONSE)
    )

    client = cube(api_url="http://localhost:4000/cubejs-api/v1")
    client.load({"measures": ["Orders.count"]}, response_format="compact")

    sent_query = json.loads(route.calls[0].request.url.params["query"])
    assert sent_query["responseFormat"] == "compact"


@respx.mock
def test_load_default_leaves_query_untouched():
    route = respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(200, json=_OK_RESPONSE)
    )

    client = cube(api_url="http://localhost:4000/cubejs-api/v1")
    client.load({"measures": ["Orders.count"]})

    sent_query = json.loads(route.calls[0].request.url.params["query"])
    assert "responseFormat" not in sent_query


@respx.mock
async def test_load_async_columnar_sets_response_format():
    route = respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(200, json=_OK_RESPONSE)
    )

    client = AsyncCubeClient(api_url="http://localhost:4000/cubejs-api/v1")
    await client.load({"measures": ["Orders.count"]}, response_format="columnar")

    sent_query = json.loads(route.calls[0].request.url.params["query"])
    assert sent_query["responseFormat"] == "columnar"
