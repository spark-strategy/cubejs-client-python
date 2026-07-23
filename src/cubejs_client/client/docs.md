# Noridoc: client

Path: @/src/cubejs_client/client

### Overview
- The Cube API client: `CubeClient` (port of `CubeApi`'s sync half) and `AsyncCubeClient` (its async twin), plus the polling/retry state machine each is built on (`run_polling_loop`/`run_polling_loop_async`, port of `CubeApi.loadMethod`).
- The integration point of the package — the only layer that imports from `core/`, `query/`, `transport/`, and `models/` all at once.

### How it fits into the larger codebase
- `__init__.py`'s `cube()` factory (@/src/cubejs_client/docs.md) constructs and returns a `CubeClient`; `AsyncCubeClient` is constructed directly (no factory) — these are the two ways users of the package obtain a client.
- Both clients take queries from @/src/cubejs_client/query/docs.md (`Query` or plain dict, normalized via `to_query_dict()`), send them through @/src/cubejs_client/transport/docs.md (`HttpTransport`/`AsyncHttpTransport` by default, or a caller-supplied `Transport`/`AsyncTransport`), decode responses with `core/response_decode.py`, and return @/src/cubejs_client/core/docs.md types (`ResultSet`, `Meta`) or `models/` types (`SqlQuery`, `ProgressResult`).

### Core Implementation
- `base.py` (`run_polling_loop` / `run_polling_loop_async`): a plain `while True` retry loop (the async version `await`s `request_fn()`/`sleep()` and additionally allows `progress_callback` to be either a sync function or a coroutine function) parameterized by a `request_fn` (called once per attempt) and a `to_result` callback (called once on a terminal, non-retryable response). Handles three retry triggers — HTTP 502 (bad gateway, retried unconditionally), a transport-reported "network error" (retried up to `network_error_retries` times), and a `"Continue wait"` error body (Cube's long-poll-in-progress signal, retried indefinitely with `progress_callback` invoked each time). Any other non-200 response raises `RequestError` (@/src/cubejs_client/errors.py). The two loops are hand-maintained twins, not shared code — a change to one's retry semantics must be mirrored in the other.
- `sync_client.py` (`CubeClient`) / `async_client.py` (`AsyncCubeClient`): constructs a default `HttpTransport`/`AsyncHttpTransport` from `api_url`/`api_token`/etc. unless a `transport` object is supplied directly. Each public method (`load`, `sql`, `meta`, `dry_run`) generates exactly **one** `baseRequestId` (a fresh UUID) before entering `_load_method` → `run_polling_loop`/`run_polling_loop_async`, and that same id is reused across every retry attempt of that logical request — only the transport-layer span counter increments per attempt (see @/src/cubejs_client/transport/docs.md).
- `load()` additionally runs `core.response_decode.decode_response_data()` on the raw response body (applying `cast_numerics` and unpacking compact/columnar formats) before constructing a `ResultSet`.

### Things to Know
- The retry architecture is **deliberately restructured** from the JS SDK's closure/`ITransportResponse.subscribe()`-based re-invocation into a plain retry loop that calls `request_fn()` again per attempt. This is functionally equivalent for the single-shot `load`/`meta`/`sql`/`dry_run` methods implemented so far, but it does not (yet) support `subscribe()`'s continuous long-poll or the JS SDK's mutex-based request-cancellation machinery (`MutexChangedError` in @/src/cubejs_client/errors.py exists as a sentinel for this but is unused until that phase).
- When `api_token` is a callable (not a string), `_update_authorization()` re-invokes it before every `_load_method` call and pushes the result onto `self._transport.authorization` — this is how token refresh is supported without the caller managing transport state directly. `AsyncCubeClient` calls the same callable synchronously (it is not itself awaited).
- `sql()`'s `to_result` branches on whether the response body is a list (blended/multi-query SQL) vs a single dict, returning `List[SqlQuery]` or a single `SqlQuery` respectively — callers must handle both return shapes.
- `async_client.py` and `sync_client.py` are not unified behind a shared base class; keeping them as separate, structurally-identical modules was a deliberate choice so each stays a straightforward, independently-readable port rather than introducing sync/async abstraction machinery for two call sites.

Created and maintained by Nori.
