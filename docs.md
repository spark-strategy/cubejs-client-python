# Noridoc: cubejs-client-python (repo root)

Path: @/

### Overview
- From-scratch Python port of the JS `@cubejs-client/core` SDK (cube-js/cube's `packages/cubejs-client-core`), tracking [cube-js/cube#1744](https://github.com/cube-js/cube/issues/1744).
- Pythonic-first public API (pandas `DataFrame` as the primary result shape, a fluent query builder, an operator-overloaded filter DSL) sitting on top of a faithful, JS-behavior-verified low-level port.
- Phases 0-3: both a synchronous (`CubeClient`) and an async (`AsyncCubeClient`) client, sharing one core; `ResultSet` covers `regularQuery`, `compareDateRangeQuery`, and `blendingQuery`. See @/src/cubejs_client/docs.md for the package's internal layering.

### How it fits into the larger codebase
- Single installable package: `src/cubejs_client/` (see @/src/cubejs_client/docs.md), built with hatchling (@/pyproject.toml).
- `tests/golden/` holds fixtures and expected outputs transcribed verbatim from the JS SDK's own `test/helpers.ts` and `test/ResultSet.test.ts`, so this port's `ResultSet`/time-series behavior is checked against real JS ground truth rather than reimplemented from scratch. `tests/unit/` covers the query builder, HTTP transport (mocked with `respx`), polling loop, and pandas adapter.
- No other packages in this repo depend on `cubejs_client` yet; it is a standalone PyPI package, independent of the cube-js/cube monorepo it ports from.

### Core Implementation
- Public entry point: `from cubejs_client import cube` — `cube(api_token, api_url=...)` returns a `CubeClient` (mirrors the JS SDK's default export). `AsyncCubeClient` (imported directly, no factory) is its async twin.
- `client.load(query)` returns a `ResultSet`; `client.meta()` returns a `Meta`; `client.sql(query)` / `client.dry_run(query)` return `SqlQuery` / raw dicts. `AsyncCubeClient` exposes the same four methods as `async def`s.
- Queries can be plain dicts (the same shape the JS SDK / Cube REST API accept) or built with `Query()`/`dim()`/`measure()` from @/src/cubejs_client/query/docs.md. Pivoting can similarly use plain dicts or the `PivotConfig` builder (@/src/cubejs_client/query/docs.md), though only `to_pandas()` accepts a `PivotConfig` directly.

### Things to Know
- Later phases — custom (PostgreSQL-interval-style) time granularities, `subscribe()`/long-polling, `cubeSql()`/streaming, the client-side `format` module, and WebSocket transport — are deferred by design, not missing functionality. They raise `NotImplementedError` or are simply absent.
- When porting new JS behavior in a later phase, port the matching JS test case's exact input/output into `tests/golden/` first (see @/README.md's "Golden tests" section) rather than reimplementing from a description of the behavior.

Created and maintained by Nori.
