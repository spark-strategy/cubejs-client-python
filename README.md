# cubejs-client-python

A Pythonic client for [Cube](https://cube.dev), the semantic layer for building
data applications. This is a from-scratch Python port of
[`@cubejs-client/core`](https://github.com/cube-js/cube/tree/master/packages/cubejs-client-core)
(tracking [cube-js/cube#1744](https://github.com/cube-js/cube/issues/1744)), not
a mechanical transliteration: pandas `DataFrame` is the primary result type, and
queries can be built with a fluent/operator DSL, while a faithful low-level core
(`ResultSet`, pivoting, time-series generation) stays behaviorally verified
against the JS SDK's own test fixtures.

**Status:** Phases 0-3 — sync (`CubeClient`) and async (`AsyncCubeClient`) clients,
both sharing one core, with `load()`/`meta()`/`sql()`/`dry_run()`; `ResultSet` covers
`regularQuery`, `compareDateRangeQuery`, and `blendingQuery` (`table_pivot`,
`chart_pivot`, `pivot`, `table_columns`, `series`/`series_names`, `decompose`, etc.);
`.to_pandas()`/`.df`; the fluent/operator query builder (`Query`, `dim()`/`measure()`);
and a `PivotConfig` builder for `to_pandas(pivot_config=...)`. Custom time
granularities, `subscribe()`, and `cubeSql()` are tracked as later phases — see the
project plan for the full roadmap. The client-side `format` module and WebSocket
transport are out of scope.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```python
from cubejs_client import cube, Query, dim

client = cube(api_token="CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")

# Plain dict query (same shape the JS SDK / REST API expects)
result_set = client.load({
    "measures": ["Orders.count"],
    "dimensions": ["Orders.status"],
})

# Or the fluent builder + operator-overloaded filter DSL
query = (
    Query()
    .measures("Orders.count")
    .dimensions("Orders.status")
    .filter(dim("Orders.status") != "cancelled")
    .order("Orders.count", "desc")
)
result_set = client.load(query)

df = result_set.to_pandas()          # pandas DataFrame, typed via table_columns()
rows = result_set.table_pivot()      # list[dict], byte-for-byte faithful to the JS SDK
```

### Async client

`AsyncCubeClient` mirrors `CubeClient` method-for-method (`load`/`meta`/`sql`/`dry_run`,
same params and query-builder support), backed by `httpx.AsyncClient`:

```python
from cubejs_client import AsyncCubeClient

client = AsyncCubeClient(api_token="CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")
result_set = await client.load({"measures": ["Orders.count"]})
df = result_set.to_pandas()
```

### PivotConfig builder

```python
from cubejs_client import PivotConfig

pivot_config = PivotConfig().x("Orders.createdAt.day").y("Orders.status", "measures")
df = result_set.to_pandas(pivot_config=pivot_config)
```

`PivotConfig` is a Pythonic convenience accepted by `to_pandas()`; `ResultSet`'s own
methods (`pivot`, `chart_pivot`, `table_pivot`, ...) stay faithful to the JS core and
take plain dicts only — call `.build()` first if calling those directly.

## Development

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest tests            # golden tests (ported from the JS SDK's own test suite) + unit tests
ruff check src tests
mypy src/cubejs_client
```

### Golden tests

`tests/golden/` contains fixtures and expected outputs transcribed verbatim
from the JS SDK's `test/helpers.ts` and `test/ResultSet.test.ts`, so the
Python `ResultSet`/time-series core can be checked against the same ground
truth the JS client is tested against. When porting new JS behavior, port the
matching JS test case's exact input/output first.
