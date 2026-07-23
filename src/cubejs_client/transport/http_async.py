"""Async twin of http_sync.py (port of HttpTransport.ts, async half).

Kept in lockstep with `HttpTransport` by hand — same URL/method/header/span
logic, `httpx.AsyncClient` instead of `httpx.Client`. See http_sync.py for
the JS semantics being preserved (GET/POST switching, Authorization without
Bearer, x-request-id span counter).
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Mapping, Optional
import json
from urllib.parse import urlencode

import httpx

from .base import RawResponse
from .http_sync import _build_stream_url_and_body


class AsyncHttpTransport:
    def __init__(
        self,
        *,
        api_url: str,
        authorization: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        credentials: Optional[str] = None,
        fetch_timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.authorization = authorization
        self.method = method
        self.headers: Dict[str, str] = dict(headers or {})
        self.credentials = credentials
        self.fetch_timeout = fetch_timeout
        self._client = client or httpx.AsyncClient()
        self._span_counters: Dict[str, int] = {}

    def _next_span_header(self, base_request_id: Optional[str]) -> Optional[str]:
        if not base_request_id:
            return None
        span = self._span_counters.get(base_request_id, 1)
        self._span_counters[base_request_id] = span + 1
        return f"{base_request_id}-span-{span}"

    async def request(self, api_method: str, params: Mapping[str, Any]) -> RawResponse:
        params = dict(params)
        method = params.pop("method", None)
        fetch_timeout = params.pop("fetchTimeout", None) or self.fetch_timeout
        base_request_id = params.pop("baseRequestId", None)
        params.pop("signal", None)

        query_params: Dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            query_params[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

        query_string = urlencode(query_params)
        url = f"{self.api_url}/{api_method}" + (f"?{query_string}" if query_string else "")

        request_method = method or self.method or ("GET" if len(url) < 2000 else "POST")

        headers = dict(self.headers)
        if request_method == "POST":
            url = f"{self.api_url}/{api_method}"
            headers["Content-Type"] = "application/json"

        if self.authorization is not None:
            headers["Authorization"] = self.authorization

        span_header = self._next_span_header(base_request_id)
        if span_header:
            headers["x-request-id"] = span_header

        timeout = (fetch_timeout / 1000) if fetch_timeout else None

        try:
            response = await self._client.request(
                request_method,
                url,
                headers=headers,
                # POST sends the original (untransformed) params as the JSON body,
                # mirroring JS's `JSON.stringify(params)` — `query_params` above is
                # only the query-string-encoded form (nested values pre-stringified),
                # and must not be reused here or nested objects get double-encoded.
                json=params if request_method == "POST" else None,
                timeout=timeout,
            )
            return RawResponse(status=response.status_code, text=response.text)
        except httpx.TimeoutException:
            return RawResponse(error="timeout")
        except httpx.HTTPError:
            return RawResponse(error="network Error")

    async def request_stream(
        self,
        api_method: str,
        *,
        params: Mapping[str, Any],
        http_method: str = "POST",
        fetch_timeout: Optional[float] = None,
        base_request_id: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Async twin of HttpTransport.request_stream — see there for semantics."""
        request_method = http_method or self.method or "POST"
        url, body = _build_stream_url_and_body(self.api_url, api_method, params, request_method)

        headers = dict(self.headers)
        if request_method == "POST":
            headers["Content-Type"] = "application/json"
        if self.authorization is not None:
            headers["Authorization"] = self.authorization
        headers["x-request-id"] = base_request_id or "stream-request"

        effective_timeout = fetch_timeout or self.fetch_timeout
        timeout = (effective_timeout / 1000) if effective_timeout else None

        async with self._client.stream(
            request_method, url, headers=headers, json=body, timeout=timeout
        ) as response:
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {response.reason_phrase}")
            async for chunk in response.aiter_bytes():
                yield chunk
