"""Port of HttpTransport.ts (sync half only; requestStream/streaming is Phase 6)."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx

from .base import RawResponse


class HttpTransport:
    def __init__(
        self,
        *,
        api_url: str,
        authorization: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Mapping[str, str]] = None,
        credentials: Optional[str] = None,
        fetch_timeout: Optional[float] = None,
        client: Optional[httpx.Client] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.authorization = authorization
        self.method = method
        self.headers: Dict[str, str] = dict(headers or {})
        self.credentials = credentials
        self.fetch_timeout = fetch_timeout
        self._client = client or httpx.Client()
        self._span_counters: Dict[str, int] = {}

    def _next_span_header(self, base_request_id: Optional[str]) -> Optional[str]:
        if not base_request_id:
            return None
        span = self._span_counters.get(base_request_id, 1)
        self._span_counters[base_request_id] = span + 1
        return f"{base_request_id}-span-{span}"

    def request(self, api_method: str, params: Mapping[str, Any]) -> RawResponse:
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
            response = self._client.request(
                request_method,
                url,
                headers=headers,
                json=query_params if request_method == "POST" else None,
                timeout=timeout,
            )
            return RawResponse(status=response.status_code, text=response.text)
        except httpx.TimeoutException:
            return RawResponse(error="timeout")
        except httpx.HTTPError:
            return RawResponse(error="network Error")
