# Noridoc: client

Path: @/src/cubejs_client/client

### Overview
- The synchronous Cube API client: `CubeClient` (port of `CubeApi`'s sync half) and the polling/retry state machine (`run_polling_loop`, port of `CubeApi.loadMethod`) it's built on.
- The integration point of the package — the only layer that imports from `core/`, `query/`, `transport/`, and `models/` all at once.

### How it fits into the larger codebase
- `__init__.py`'s `cube()` factory (@/src/cubejs_client/docs.md) constructs and returns a `CubeClient` — this is the primary way users of the package obtain a client.
- `CubeClient` takes queries from @/src/cubejs_client/query/docs.md (`Query` or plain dict, normalized via `to_query_dict()`), sends them through @/src/cubejs_client/transport/docs.md (`HttpTransport` by default, or a caller-supplied `Transport`), decodes responses with `core/response_decode.py`, and returns @/src/cubejs_client/core/docs.md types (`ResultSet`, `Meta`) or `models/` types (`SqlQuery`, `ProgressResult`).

### Core Implementation
- `base.py` (`run_polling_loop`): a plain `while True` retry loop parameterized by a `request_fn` (called once per attempt) and a `to_result` callback (called once on a terminal, non-retryable response). Handles three retry triggers — HTTP 502 (bad gateway, retried unconditionally), a transport-reported "network error" (retried up to `network_error_retries` times), and a `"Continue wait"` error body (Cube's long-poll-in-progress signal, retried indefinitely with `progress_callback` invoked each time). Any other non-200 response raises `RequestError` (@/src/cubejs_client/errors.py).
- `sync_client.py` (`CubeClient`): constructs a default `HttpTransport` from `api_url`/`api_token`/etc. unless a `transport` object is supplied directly. Each public method (`load`, `sql`, `meta`, `dry_run`) generates exactly **one** `baseRequestId` (a fresh UUID) before entering `_load_method` → `run_polling_loop`, and that same id is reused across every retry attempt of that logical request — only the transport-layer span counter increments per attempt (see @/src/cubejs_client/transport/docs.md).
- `load()` additionally runs `core.response_decode.decode_response_data()` on the raw response body (applying `cast_numerics` and unpacking compact/columnar formats) before constructing a `ResultSet`.

### Things to Know
- The retry architecture is **deliberately restructured** from the JS SDK's closure/`ITransportResponse.subscribe()`-based re-invocation into a plain synchronous retry loop that calls `request_fn()` again per attempt. This is functionally equivalent for the single-shot `load`/`meta`/`sql`/`dry_run` methods implemented so far, but it does not (yet) support `subscribe()`'s continuous long-poll or the JS SDK's mutex-based request-cancellation machinery (`MutexChangedError` in @/src/cubejs_client/errors.py exists as a sentinel for this but is unused until that phase).
- When `api_token` is a callable (not a string), `CubeClient._update_authorization()` re-invokes it before every `_load_method` call and pushes the result onto `self._transport.authorization` — this is how token refresh is supported without the caller managing transport state directly.
- `sql()`'s `to_result` branches on whether the response body is a list (blended/multi-query SQL) vs a single dict, returning `List[SqlQuery]` or a single `SqlQuery` respectively — callers must handle both return shapes.

Created and maintained by Nori.
