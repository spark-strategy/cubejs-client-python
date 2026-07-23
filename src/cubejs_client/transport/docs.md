# Noridoc: transport

Path: @/src/cubejs_client/transport

### Overview
- The HTTP contract for talking to a Cube deployment's REST API: minimal `Transport`/`AsyncTransport` protocols plus `HttpTransport`/`AsyncHttpTransport`, ports of the JS SDK's `HttpTransport.ts` (sync and async halves, `httpx.Client`/`httpx.AsyncClient` respectively).
- One HTTP call in, one `RawResponse` out — no retry/polling logic lives here; that belongs to @/src/cubejs_client/client/docs.md, which calls `Transport.request()`/`AsyncTransport.request()` repeatedly.

### How it fits into the larger codebase
- `client/sync_client.py` (@/src/cubejs_client/client/docs.md) constructs an `HttpTransport` by default (or accepts a caller-supplied object satisfying the `Transport` protocol) and passes it into `run_polling_loop()`, which calls `.request(method, params)` once per attempt. `client/async_client.py` does the same with `AsyncHttpTransport`/`AsyncTransport`/`run_polling_loop_async()`.
- `errors.py`'s `RequestError` is raised by the *caller* (`client/base.py`) based on the `RawResponse` this layer returns — `transport/` itself never raises on HTTP-level errors, it only reports them via `RawResponse.error`/`.status`.

### Core Implementation
- `base.py`: `RawResponse(status, text, error)` and the `Transport`/`AsyncTransport` protocols (`request(method, params) -> RawResponse`, the latter `async`, plus a mutable `authorization` attribute the client updates when the API token is a callable).
- `http_sync.py` (`HttpTransport`) / `http_async.py` (`AsyncHttpTransport`): built and kept in lockstep by hand — same URL/method/header/span logic, one using `httpx.Client`, the other `httpx.AsyncClient`. Both build the request URL/method/headers from `params`; GET is used when the resulting URL is under 2000 characters, POST otherwise (mirroring the JS SDK's exact threshold). Query-string values that are dicts/lists are individually JSON-serialized before being URL-encoded; for POST, the *original* `params` dict (not the query-string-encoded form) is passed as `httpx`'s `json=` body, matching JS's `JSON.stringify(params)` — reusing the query-string-encoded values there would double-encode nested objects like `query`.

### Things to Know
- The `Authorization` header is set to the raw token string with **no `"Bearer "` prefix** — this matches the JS SDK's behavior, not standard OAuth Bearer-token convention. Callers supplying their own token format must account for this.
- `x-request-id` is built from a caller-supplied `baseRequestId` plus a per-`baseRequestId` span counter (`self._span_counters`, incrementing on every `.request()` call with that same base id). This exists because Python's plain retry loop (see @/src/cubejs_client/client/docs.md) re-invokes `request()` per attempt instead of using JS's closure/subscribe-based retry, so the span counter is this layer's replacement mechanism for keeping retries of the same logical request traceable/correlated server-side.
- `httpx.TimeoutException` and other `httpx.HTTPError`s are caught here and converted into `RawResponse(error=...)` rather than propagating as exceptions — this is a deliberate boundary: `.request()` never raises for ordinary network failures, so the polling loop can treat all failure modes (timeout, network error, non-200 status) uniformly via `RawResponse` fields.
- `requestStream`/streaming transport (used by `cubeSql()`) is explicitly out of scope for this phase.

Created and maintained by Nori.
