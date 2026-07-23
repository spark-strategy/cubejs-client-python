# Noridoc: cubejs_client package

Path: @/src/cubejs_client

### Overview
- The installable package. Its internal layering mirrors the design goal stated in @/README.md: a faithful, JS-verified core wrapped in a Pythonic surface.
- Four layers, each with its own docs.md: pure/transport-free @/src/cubejs_client/core/docs.md at the bottom, @/src/cubejs_client/query/docs.md for building queries, @/src/cubejs_client/transport/docs.md + @/src/cubejs_client/client/docs.md for talking to a Cube deployment, and @/src/cubejs_client/results/docs.md as a pandas convenience layer bolted on top of the core.
- `errors.py` (`CubeError`, `RequestError`, `MutexChangedError`) and `models/` (`SqlQuery`, `ProgressResult`) are small, self-contained ports of `RequestError.ts`, `SqlQuery.ts`, and `ProgressResult.ts` used across the other layers — not broken out into their own docs.md.

### How it fits into the larger codebase
```
query/  (Query, dim/measure DSL, validate, PivotConfig)
   \
    -> client/sync_client.py  (CubeClient)      -> transport/http_sync.py  (HttpTransport)  -> Cube REST API
    -> client/async_client.py (AsyncCubeClient) -> transport/http_async.py (AsyncHttpTransport) -> Cube REST API
                |                                  |
                v                                  v
        core/result_set.py (ResultSet)     client/base.py (run_polling_loop / run_polling_loop_async)
                |
                v
        results/pandas_adapter.py  (monkey-patches ResultSet.to_pandas / .df)
```
- `__init__.py` is the only place that wires all layers together: it imports `CubeClient`, `AsyncCubeClient`, `Meta`, `ResultSet`, `PivotConfig`, the query DSL, and — critically — `results.pandas_adapter`, whose import has the side effect of attaching `to_pandas()`/`.df` onto the `ResultSet` class. Nothing else imports `results.pandas_adapter`.
- `client/sync_client.py` and `client/async_client.py` are the only modules that import from every other layer (`core`, `query`, `transport`, `models`) — they are the integration points, not `core`. The two are kept in lockstep by hand, method-for-method, rather than sharing a base class.

### Core Implementation
- Entry point: `cube(api_token, api_url=...)` factory in `__init__.py`, returning a `CubeClient` (@/src/cubejs_client/client/docs.md); `AsyncCubeClient` is constructed directly (no factory).
- A `load()` call flows: caller's `Query`/dict -> `to_query_dict()` (@/src/cubejs_client/query/docs.md) -> `CubeClient.load()`/`AsyncCubeClient.load()` builds request params -> `run_polling_loop()`/`run_polling_loop_async()` (@/src/cubejs_client/client/docs.md) repeatedly calls `Transport.request()` (@/src/cubejs_client/transport/docs.md) -> response body passed through `decode_response_data()` -> wrapped in a `ResultSet` (@/src/cubejs_client/core/docs.md) -> caller optionally calls `.to_pandas()`/`.df` (@/src/cubejs_client/results/docs.md), optionally passing a `PivotConfig` (@/src/cubejs_client/query/docs.md).
- `Meta`, `SqlQuery`, and `ProgressResult` are simpler value-object ports returned by `meta()`, `sql()`, and progress callbacks respectively; they hold a raw response dict and expose typed accessor methods rather than doing any transformation.

### Things to Know
- `core/` is deliberately kept free of both a network transport and a pandas dependency — it is the part golden-tested against the JS SDK's own fixtures (@/tests/golden), and keeping it dependency-light keeps that verification surface small and independently testable.
- The pandas attachment in `results/pandas_adapter.py` is monkey-patching, not subclassing or composition — this was a deliberate choice to let `core.result_set.ResultSet` be usable standalone (no pandas import) while still presenting `to_pandas()`/`.df` as ordinary methods/properties on the same public `ResultSet` class importable from `cubejs_client`. Do not add pandas imports inside `core/`.

Created and maintained by Nori.
