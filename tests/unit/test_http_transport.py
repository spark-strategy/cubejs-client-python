import httpx
import respx

from cubejs_client.transport.http_sync import HttpTransport


@respx.mock
def test_get_request_with_json_encoded_query_param():
    route = respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    transport = HttpTransport(api_url="http://localhost:4000/cubejs-api/v1", authorization="TOKEN")
    response = transport.request("load", {"query": {"measures": ["Orders.count"]}})

    assert route.called
    sent = route.calls[0].request
    assert sent.url.params["query"] == '{"measures": ["Orders.count"]}'
    assert response.status == 200


@respx.mock
def test_authorization_header_has_no_bearer_prefix():
    route = respx.get("http://localhost:4000/cubejs-api/v1/meta").mock(
        return_value=httpx.Response(200, json={"cubes": []})
    )

    transport = HttpTransport(api_url="http://localhost:4000/cubejs-api/v1", authorization="RAW-JWT-TOKEN")
    transport.request("meta", {})

    sent = route.calls[0].request
    assert sent.headers["Authorization"] == "RAW-JWT-TOKEN"


@respx.mock
def test_forced_post_method_sends_json_body_with_content_type():
    route = respx.post("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    transport = HttpTransport(api_url="http://localhost:4000/cubejs-api/v1")
    transport.request("load", {"query": {"measures": ["Orders.count"]}, "method": "POST"})

    sent = route.calls[0].request
    assert sent.headers["content-type"] == "application/json"
    assert sent.url.params.get("query") is None


@respx.mock
def test_x_request_id_span_counter_increments_per_call():
    respx.get("http://localhost:4000/cubejs-api/v1/load").mock(return_value=httpx.Response(200, json={}))

    transport = HttpTransport(api_url="http://localhost:4000/cubejs-api/v1")
    transport.request("load", {"baseRequestId": "req-1"})
    transport.request("load", {"baseRequestId": "req-1"})

    calls = respx.calls
    assert calls[0].request.headers["x-request-id"] == "req-1-span-1"
    assert calls[1].request.headers["x-request-id"] == "req-1-span-2"


@respx.mock
def test_non_200_status_is_surfaced_without_raising():
    respx.get("http://localhost:4000/cubejs-api/v1/load").mock(
        return_value=httpx.Response(403, json={"error": "Forbidden"})
    )

    transport = HttpTransport(api_url="http://localhost:4000/cubejs-api/v1")
    response = transport.request("load", {})

    assert response.status == 403
    assert "Forbidden" in response.text
