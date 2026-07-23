# `cubejs-client-python` API Reference

A Pythonic client for [Cube](https://cube.dev). This is a from-scratch Python port of
[`@cubejs-client/core`](https://github.com/cube-js/cube/tree/master/packages/cubejs-client-core),
not a mechanical transliteration: pandas `DataFrame` is a first-class result type and queries
can be built with a fluent/operator DSL, while the low-level `ResultSet`/pivot/time-series
core stays behaviorally faithful to the JS SDK (verified against its own test fixtures).

All examples below show **real output** produced by the library.

---

## Documentation Index

| Section | Contents |
| --- | --- |
| [Getting started](#getting-started) | Install, quick start |
| [`cube`](#cube) | Factory function |
| [`CubeClient`](#cubeclient) | Synchronous client |
| [`AsyncCubeClient`](#asynccubeclient) | Asynchronous client |
| [`Subscription`](#subscription) / [`AsyncSubscription`](#asyncsubscription) | Subscription handles |
| [`ResultSet`](#resultset) | Query results, pivoting, pandas |
| [`Meta`](#meta) | Data-model metadata |
| [`SqlQuery`](#sqlquery) | Generated SQL |
| [`ProgressResult`](#progressresult) | Long-query progress |
| [`Query`](#query) | Fluent query builder |
| [`PivotConfig`](#pivotconfig) | Fluent pivot-config builder |
| [`dim` / `measure` / `Member` / `Filter`](#dim--measure) | Operator filter DSL |
| [Query utilities](#query-utilities) | `validate_query`, etc. |
| [Transports](#transports) | `HttpTransport`, `AsyncHttpTransport`, protocols |
| [Errors](#errors) | Exception hierarchy |
| [Types](#types) | Result/config shapes |
| [Differences from the JS SDK](#differences-from-the-js-sdk) | Divergences and omissions |

---

## Getting started

```bash
pip install -e ".[dev]"
```

```python
from cubejs_client import cube

client = cube("CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")
result_set = client.load({"measures": ["Orders.count"], "dimensions": ["Orders.status"]})

df = result_set.to_pandas()      # pandas DataFrame
rows = result_set.table_pivot()  # list[dict], faithful to the JS SDK
```

---

## `cube`

> **cube**(api_token: `Optional[Union[str, Callable[[], str]]]` = None, api_url: `Optional[str]` = None, `**kwargs`) → *[CubeClient](#cubeclient)*

Factory mirroring the JS SDK's default export. `api_token` may be a string or a zero-arg
callable returning a token (re-invoked before each request, so it can refresh). Extra keyword
arguments are forwarded to the [`CubeClient`](#cubeclient) constructor.

```python
from cubejs_client import cube

client = cube("CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")

# Token provider (called before every request)
client = cube(lambda: get_jwt(), api_url="http://localhost:4000/cubejs-api/v1")
```

---

## `CubeClient`

The synchronous API entry point.

### Constructor

> **CubeClient**(api_token=None, `*`, api_url=None, transport=None, headers=None, method=None, credentials=None, fetch_timeout=None, poll_interval=5.0, cast_numerics=False, parse_date_measures=False, network_error_retries=0)

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `api_token` | `str \| Callable[[], str]` | ✅ | JWT, or a callable returning one. Sent as `Authorization` (no `Bearer` prefix). |
| `api_url` | `str` | ✅ | e.g. `http://localhost:4000/cubejs-api/v1`. Required unless `transport` is given. |
| `transport` | [`Transport`](#transport-protocols) | ✅ | Custom transport. Defaults to [`HttpTransport`](#httptransport). |
| `headers` | `dict` | ✅ | Extra HTTP headers. |
| `method` | `str` | ✅ | Force `"GET"` or `"POST"`. Default: GET when the URL is < 2000 chars, else POST. |
| `credentials` | `str` | ✅ | Passed through to the transport. |
| `fetch_timeout` | `float` | ✅ | Request timeout in **milliseconds**. |
| `poll_interval` | `float` | ✅ | Seconds between polls while a query is running. Default `5.0`. |
| `cast_numerics` | `bool` | ✅ | Cast `type: "number"` members to numerics during decode. Default `False`. |
| `parse_date_measures` | `bool` | ✅ | Parse date-typed measures. Default `False`. |
| `network_error_retries` | `int` | ✅ | Retries for transport-level failures. Default `0`. |

### `load`

> **load**(query, `*`, cast_numerics=None, parse_date_measures=None, cache=None, response_format="default", progress_callback=None) → *[ResultSet](#resultset)*

Run a query and return a `ResultSet`. Polls transparently while the server responds
`Continue wait`.

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `query` | `dict` or [`Query`](#query) | | The query. |
| `cast_numerics` | `bool` | ✅ | Per-call override of the client default. |
| `parse_date_measures` | `bool` | ✅ | Per-call override of the client default. |
| `cache` | `str` | ✅ | Cache-control hint forwarded to the API. |
| `response_format` | `str` | ✅ | `"default"`, `"compact"`, or `"columnar"`. Non-default values stamp `responseFormat` onto the outgoing query; all formats are decoded transparently. |
| `progress_callback` | `Callable[[ProgressResult], None]` | ✅ | Called on each `Continue wait` poll with a [`ProgressResult`](#progressresult). |

```python
result_set = client.load({"measures": ["Orders.count"]})
result_set = client.load(Query().measures("Orders.count"), response_format="compact")
```

### `sql`

> **sql**(query) → *[SqlQuery](#sqlquery) | List[[SqlQuery](#sqlquery)]*

Return the SQL Cube would generate for `query`.

### `meta`

> **meta**() → *[Meta](#meta)*

Fetch the data model (cubes, measures, dimensions, segments).

### `dry_run`

> **dry_run**(query) → *dict*

Return query metadata (normalized queries, pivot query, query order, transformed queries)
without executing it.

### `subscribe`

> **subscribe**(query, callback, `*`, cast_numerics=None, parse_date_measures=None, cache=None) → *[Subscription](#subscription)*

Poll `query` on an interval, invoking `callback(error, result_set)` for each update. Runs on a
daemon thread and returns immediately.

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `query` | `dict` or [`Query`](#query) | | The query. |
| `callback` | `Callable[[error, result_set], Any]` | | Receives `(None, result_set)` on success, `(error, None)` on failure, where `error` is a [`RequestError`](#errors). |

Request errors are delivered to the callback and **do not** stop the loop. If the callback
raises, the loop stops and the exception is re-raised from `unsubscribe()`.

```python
def on_update(error, result_set):
    if error is None:
        print(result_set.table_pivot())

subscription = client.subscribe({"measures": ["Logs.count"]}, on_update)
subscription.unsubscribe()
```

### `cube_sql`

> **cube_sql**(sql_query: `str`, `*`, timeout=None, cache=None) → *dict*

Execute a raw SQL string against the Cube SQL interface.

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `sql_query` | `str` | | SQL to execute. |
| `timeout` | `float` | ✅ | Query timeout in **milliseconds**. |
| `cache` | `str` | ✅ | Cache-control hint. |

Returns `{"schema": [...], "data": [...], "lastRefreshTime"?: str}` — see
[`CubeSqlResult`](#cubesqlresult).

```python
result = client.cube_sql("SELECT status, measure(count) FROM orders GROUP BY 1")
for row in result["data"]:
    print(row)
```

### `cube_sql_stream`

> **cube_sql_stream**(sql_query: `str`, `*`, timeout=None, cache=None) → *Iterator[dict]*

Stream CubeSQL results as typed chunks (see [`CubeSqlStreamChunk`](#cubesqlstreamchunk)).
Raises `RuntimeError` if the transport has no streaming support.

```python
for chunk in client.cube_sql_stream("SELECT * FROM orders"):
    if chunk["type"] == "data":
        print(chunk["data"])
```

> **Note:** consume the generator fully, or close it if you stop early, so the underlying HTTP
> stream closes deterministically instead of waiting on GC.

---

## `AsyncCubeClient`

Mirrors [`CubeClient`](#cubeclient) method-for-method, backed by `httpx.AsyncClient`. The
constructor takes the same arguments (with an `AsyncTransport`).

| Method | Signature |
| --- | --- |
| `load` | `async load(query, *, cast_numerics=None, parse_date_measures=None, cache=None, response_format="default", progress_callback=None)` → *[ResultSet](#resultset)* |
| `sql` | `async sql(query)` → *[SqlQuery](#sqlquery) \| List[SqlQuery]* |
| `meta` | `async meta()` → *[Meta](#meta)* |
| `dry_run` | `async dry_run(query)` → *dict* |
| `cube_sql` | `async cube_sql(sql_query, *, timeout=None, cache=None)` → *dict* |
| `cube_sql_stream` | `cube_sql_stream(sql_query, *, timeout=None, cache=None)` → *AsyncIterator[dict]* (async generator) |
| `subscribe` | `subscribe(query, callback, ...)` → *[AsyncSubscription](#asyncsubscription)* (**not** a coroutine) |

`progress_callback` and the `subscribe` callback may be sync or async.

```python
from cubejs_client import AsyncCubeClient

client = AsyncCubeClient("CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")
result_set = await client.load({"measures": ["Orders.count"]})

async for chunk in client.cube_sql_stream("SELECT * FROM orders"):
    ...

subscription = client.subscribe({"measures": ["Logs.count"]}, on_update)  # no await
await subscription.unsubscribe()
```

---

## `Subscription`

Handle returned by `CubeClient.subscribe`. Replaces the JS `UnsubscribeObj`.

> **unsubscribe**(timeout: `Optional[float]` = None) → *None*

Stops the poll loop and joins the worker thread. Returns promptly even with a large
`poll_interval` (the wait is interruptible). Re-raises any exception the callback raised.

| Attribute | Type | Description |
| --- | --- | --- |
| `exception` | `Optional[BaseException]` | Exception raised by the callback, if any. |

## `AsyncSubscription`

Handle returned by `AsyncCubeClient.subscribe`.

> `async` **unsubscribe**() → *None*

Sets the stop flag, cancels the task, awaits it, and re-raises any callback exception.
Exposes the same `exception` attribute.

---

## `ResultSet`

Wraps a load response and provides the pivoting/formatting API. Constructed for you by
`load()`.

> **ResultSet**(load_response: `Mapping[str, Any]`, options: `Optional[dict]` = None)

All pivot-taking methods accept an optional `pivot_config` **dict** (see
[`PivotConfig` (dict shape)](#pivotconfig-dict-shape)). They intentionally do **not** accept a
[`PivotConfig`](#pivotconfig) builder object — call `.build()` first, or use `to_pandas()`,
which does accept it.

The examples below all use this response: measure `Orders.count`, dimension `Orders.status`,
time dimension `Orders.createdAt` at `month` granularity.

### `raw_data`

> **raw_data**() → *list*

The rows exactly as the API returned them.

```python
[
  {"Orders.createdAt.month": "2020-01-01T00:00:00.000", "Orders.createdAt": "2020-01-01T00:00:00.000",
   "Orders.status": "completed", "Orders.count": "10"},
  {"Orders.createdAt.month": "2020-02-01T00:00:00.000", "Orders.createdAt": "2020-02-01T00:00:00.000",
   "Orders.status": "shipped", "Orders.count": "5"}
]
```

### `table_pivot`

> **table_pivot**(pivot_config=None) → *list*

Rows as flat dicts, suitable for a table. Values keep their original types (strings stay
strings; missing values stay `None`).

```python
[
  {"Orders.createdAt.month": "2020-01-01T00:00:00.000", "Orders.status": "completed", "Orders.count": "10"},
  {"Orders.createdAt.month": "2020-02-01T00:00:00.000", "Orders.status": "shipped", "Orders.count": "5"}
]
```

### `chart_pivot`

> **chart_pivot**(pivot_config=None) → *list*

Rows shaped for charting. Measure values are coerced to numbers (JS `parseFloat` semantics),
and gaps become `0`.

```python
[
  {"x": "2020-01-01T00:00:00.000", "xValues": ["2020-01-01T00:00:00.000"],
   "completed,Orders.count": 10.0, "shipped,Orders.count": 0},
  {"x": "2020-02-01T00:00:00.000", "xValues": ["2020-02-01T00:00:00.000"],
   "completed,Orders.count": 0, "shipped,Orders.count": 5.0}
]
```

### `pivot`

> **pivot**(pivot_config=None) → *list*

The low-level pivot: `xValues` plus `yValuesArray` pairs of `[yValues, value]`.

```python
[
  {"xValues": ["2020-01-01T00:00:00.000"],
   "yValuesArray": [[["completed", "Orders.count"], "10"], [["shipped", "Orders.count"], 0]]},
  {"xValues": ["2020-02-01T00:00:00.000"],
   "yValuesArray": [[["completed", "Orders.count"], 0], [["shipped", "Orders.count"], "5"]]}
]
```

### `table_columns`

> **table_columns**(pivot_config=None) → *list*

Column descriptors for a table. See [`TableColumn`](#tablecolumn).

```python
[
  {"key": "Orders.createdAt.month", "title": "Orders Created at", "shortTitle": "Created at",
   "type": "time", "format": None, "meta": None, "currency": None, "granularity": None,
   "dataIndex": "Orders.createdAt.month"},
  {"key": "Orders.status", "title": "Orders Status", "shortTitle": "Status", "type": "string",
   "format": None, "meta": None, "currency": None, "granularity": None, "dataIndex": "Orders.status"},
  {"key": "Orders.count", "type": "number", "format": None, "meta": None, "currency": None,
   "granularity": None, "dataIndex": "Orders.count", "title": "Orders Count", "shortTitle": "Count"}
]
```

### `series`

> **series**(pivot_config=None) → *list*

One entry per series, each with its `(x, value)` points.

```python
[
  {"title": "completed, Orders Count", "shortTitle": "completed, Count", "key": "completed,Orders.count",
   "series": [{"value": 10.0, "x": "2020-01-01T00:00:00.000"},
              {"value": 0,    "x": "2020-02-01T00:00:00.000"}]},
  {"title": "shipped, Orders Count", "shortTitle": "shipped, Count", "key": "shipped,Orders.count",
   "series": [{"value": 0,   "x": "2020-01-01T00:00:00.000"},
              {"value": 5.0, "x": "2020-02-01T00:00:00.000"}]}
]
```

### `series_names`

> **series_names**(pivot_config=None) → *list*

Series identity without the data points.

```python
[
  {"title": "completed, Orders Count", "shortTitle": "completed, Count",
   "key": "completed,Orders.count", "yValues": ["completed", "Orders.count"]},
  {"title": "shipped, Orders Count", "shortTitle": "shipped, Count",
   "key": "shipped,Orders.count", "yValues": ["shipped", "Orders.count"]}
]
```

### `categories`

> **categories**(pivot_config=None) → *list*

Alias of [`chart_pivot`](#chart_pivot).

### `total_row`

> **total_row**(pivot_config=None) → *dict*

A single aggregated row in `chart_pivot` shape.

### `total_rows`

> **total_rows**() → *Optional[int]*

The server-reported total row count (`None` when the query didn't request totals).

### `query`

> **query**() → *dict*

The normalized query that produced this result.

### `pivot_query`

> **pivot_query**() → *Optional[dict]*

The pivot query (the query plus `queryType`).

### `annotation`

> **annotation**() → *dict*

Title/type metadata for `measures`, `dimensions`, `segments`, and `timeDimensions`.

### `drill_down`

> **drill_down**(drill_down_locator: `Mapping[str, Any]`, pivot_config=None) → *Optional[dict]*

Build a drill-down query for a specific cell, located by `xValues`/`yValues`. Returns `None`
when the measure declares no `drillMembers`. Raises `ValueError` for
`compareDateRangeQuery`/`blendingQuery` result sets.

```python
query = result_set.drill_down({"xValues": ["2020-01-01T00:00:00.000"], "yValues": ["completed"]})
if query is not None:
    detail = client.load(query)
```

### `decompose`

> **decompose**() → *List[[ResultSet](#resultset)]*

Split a `compareDateRangeQuery`/`blendingQuery` result into one `ResultSet` per sub-result.

### `time_series`

> **time_series**(time_dimension: `Mapping[str, Any]`, result_index=None, annotations=None) → *Optional[list]*

Generate the time-series axis for a time dimension. Supports predefined granularities and
custom (PostgreSQL-interval-style) granularities — the latter needs `annotations` to resolve
the interval/origin/offset.

### `serialize` / `deserialize`

> **serialize**() → *dict*
> `static` **deserialize**(data: `Mapping[str, Any]`, options=None) → *[ResultSet](#resultset)*

Round-trip a `ResultSet` through a plain dict.

### `to_pandas`

> **to_pandas**(pivot_config: `PivotConfig | dict | None` = None, kind: `str` = `"table"`) → *`pandas.DataFrame`*

Convert to a DataFrame. `kind` is `"table"` (uses `table_pivot`, typed via `table_columns`) or
`"chart"` (uses `chart_pivot`). Accepts a [`PivotConfig`](#pivotconfig) builder **or** a dict.

### `df`

> *property* **df** → *`pandas.DataFrame`*

Cached `to_pandas()` with defaults.

```python
>>> result_set.df
  Orders.createdAt.month Orders.status  Orders.count
0             2020-01-01     completed            10
1             2020-02-01       shipped             5
```

### Static helpers

| Method | Signature | Description |
| --- | --- | --- |
| `get_normalized_pivot_config` | `(query=None, pivot_config=None)` → *dict* | Fill in default `x`/`y` axes for a query. |
| `normalize_pivot_config` | `(self, pivot_config=None)` → *dict* | Instance form, using this result's pivot query. |
| `measure_from_axis` | `(axis_values: Sequence[Any])` → *Any* | Extract the measure name from axis values. |
| `time_dimension_member` | `(td: Mapping[str, Any])` → *str* | `"Cube.dim.granularity"` key for a time dimension. |

---

## `Meta`

Wraps the `/meta` response.

> **Meta**(meta_response: `Mapping[str, Any]`)

### `members_for_query`

> **members_for_query**(_query, member_type: `str`) → *list*

All members of `member_type` (`"measures"`, `"dimensions"`, `"segments"`), sorted by title.

```python
[{"name": "Orders.count", "title": "Orders Count", "shortTitle": "Count", "type": "number"}]
```

### `members_grouped_by_cube`

> **members_grouped_by_cube**() → *Dict[str, List[dict]]*

Members grouped per cube, keyed by `measures` / `dimensions` / `segments` / `timeDimensions`
(the last filtered from `dimensions` by `type == "time"`).

```python
{
  "measures": [
    {"cubeName": "Orders", "cubeTitle": "Orders", "type": "cube", "public": True,
     "members": [{"name": "Orders.count", "title": "Orders Count", "shortTitle": "Count", "type": "number"}]}
  ],
  "dimensions": [...], "segments": [...], "timeDimensions": [...]
}
```

`type` and `public` are `None` when the cube omits them.

### `resolve_member`

> **resolve_member**(member_name: `str`, member_type: `str | Sequence[str]`) → *dict*

Look up a member's metadata. Returns an error-shaped dict when not found:

```python
>>> meta.resolve_member("Orders.status", "dimensions")
{"name": "Orders.status", "title": "Orders Status", "shortTitle": "Status", "type": "string"}

>>> meta.resolve_member("Nope.x", "dimensions")
{"title": "Nope.x", "error": "Cube not found Nope for path 'Nope.x'"}
```

### `filter_operators_for_member`

> **filter_operators_for_member**(member_name: `str`, member_type: `str | Sequence[str]`) → *List[dict]*

Filter operators valid for a member's type.

```python
[{"name": "contains", "title": "contains"},
 {"name": "notContains", "title": "does not contain"},
 {"name": "equals", "title": "equals"}, ...]
```

### `default_time_dimension_name_for`

> **default_time_dimension_name_for**(member_name: `str`) → *Optional[str]*

The first `type: "time"` dimension of the given cube, e.g. `"Orders.createdAt"`.

---

## `SqlQuery`

> **SqlQuery**(sql_query_wrapper: `Mapping[str, Any]`)

| Method | Returns | Description |
| --- | --- | --- |
| `raw_query()` | *dict* | The full `sql` payload. |
| `sql()` | *str* | The SQL string. |

## `ProgressResult`

Passed to `progress_callback` while a query is running.

| Method | Returns | Description |
| --- | --- | --- |
| `stage()` | *str* | Current stage, e.g. `"Executing query"`. |
| `time_elapsed()` | *float* | Milliseconds elapsed. |

---

## `Query`

Immutable, fluent query builder. Every method returns a **new** `Query`.

| Method | Signature |
| --- | --- |
| `measures` | `(*names: str \| Iterable[str])` → *Query* |
| `dimensions` | `(*names: str \| Iterable[str])` → *Query* |
| `segments` | `(*names: str \| Iterable[str])` → *Query* |
| `time_dimension` | `(dimension: str, granularity=None, date_range=None)` → *Query* |
| `filter` | `(*filters: Mapping[str, Any])` → *Query* |
| `order` | `(member: str, direction: str = "asc")` → *Query* |
| `limit` | `(n: int)` → *Query* |
| `offset` | `(n: int)` → *Query* |
| `timezone` | `(tz: str)` → *Query* |
| `total` | `(flag: bool = True)` → *Query* |
| `build` | `()` → *dict* |

```python
from cubejs_client import Query, dim

q = (Query()
     .measures("Orders.count")
     .dimensions("Orders.status")
     .time_dimension("Orders.createdAt", granularity="month", date_range="last 30 days")
     .filter(dim("Orders.status") != "cancelled")
     .order("Orders.count", "desc")
     .limit(100))
```

`q.build()` produces:

```python
{
  "measures": ["Orders.count"],
  "dimensions": ["Orders.status"],
  "timeDimensions": [{"dimension": "Orders.createdAt", "granularity": "month", "dateRange": "last 30 days"}],
  "filters": [{"member": "Orders.status", "operator": "notEquals", "values": ["cancelled"]}],
  "order": [["Orders.count", "desc"]],
  "limit": 100
}
```

---

## `PivotConfig`

Immutable, fluent builder for pivot configuration.

| Method | Signature |
| --- | --- |
| `x` | `(*members: str \| Iterable[str])` → *PivotConfig* |
| `y` | `(*members: str \| Iterable[str])` → *PivotConfig* |
| `fill_missing_dates` | `(flag: bool = True)` → *PivotConfig* |
| `join_date_range` | `(flag: bool = True)` → *PivotConfig* |
| `fill_with_value` | `(value: Any)` → *PivotConfig* |
| `alias_series` | `(*names: str \| Iterable[str])` → *PivotConfig* |
| `build` | `()` → *dict* |

```python
from cubejs_client import PivotConfig

pc = PivotConfig().x("Orders.createdAt.month").y("Orders.status", "measures").fill_missing_dates(True)
df = result_set.to_pandas(pivot_config=pc)
```

`pc.build()` produces:

```python
{"x": ["Orders.createdAt.month"], "y": ["Orders.status", "measures"], "fillMissingDates": True}
```

> An explicitly-built `PivotConfig()` lowers to `{}`, never `None`, mirroring the JS
> `pivotConfig || {default}` semantics.

---

## `dim` / `measure`

> **dim**(name: `str`) → *[Member](#member)*
> **measure**(name: `str`) → *[Member](#member)*

Create a `Member` for the operator filter DSL. Both are identical; use whichever reads better.

### `Member`

Comparison operators and methods return a [`Filter`](#filter).

| Expression | Operator emitted |
| --- | --- |
| `m == v` | `equals` |
| `m != v` | `notEquals` |
| `m < v` | `lt` |
| `m <= v` | `lte` |
| `m > v` | `gt` |
| `m >= v` | `gte` |
| `m.is_in(*v)` | `equals` |
| `m.not_in(*v)` | `notEquals` |
| `m.contains(*v)` | `contains` |
| `m.not_contains(*v)` | `notContains` |
| `m.starts_with(*v)` | `startsWith` |
| `m.not_starts_with(*v)` | `notStartsWith` |
| `m.ends_with(*v)` | `endsWith` |
| `m.not_ends_with(*v)` | `notEndsWith` |
| `m.is_set()` | `set` (no `values`) |
| `m.is_not_set()` | `notSet` (no `values`) |
| `m.in_date_range(start, end)` | `inDateRange` |
| `m.not_in_date_range(start, end)` | `notInDateRange` |
| `m.before_date(d)` | `beforeDate` |
| `m.before_or_on_date(d)` | `beforeOrOnDate` |
| `m.after_date(d)` | `afterDate` |
| `m.after_or_on_date(d)` | `afterOrOnDate` |

All values are stringified, matching the API contract:

```python
>>> dim("Users.age") >= 21
{"member": "Users.age", "operator": "gte", "values": ["21"]}

>>> dim("Users.email").is_set()
{"member": "Users.email", "operator": "set"}
```

### `Filter`

Combine filters with `&` and `|`:

```python
>>> (dim("a") == "1") & (dim("b") == "2")
{"and": [{"member": "a", "operator": "equals", "values": ["1"]},
         {"member": "b", "operator": "equals", "values": ["2"]}]}

>>> (dim("a") == "1") | (dim("b") == "2")
{"or": [...]}
```

> **Gotcha:** Python evaluates `and`/`or` with truthiness — always use `&` and `|`, and
> parenthesize operands (`&`/`|` bind tighter than comparisons).

---

## Query utilities

| Function | Signature | Description |
| --- | --- | --- |
| `validate_query` | `(query)` → *dict* | Drop filters without an `operator` and time dimensions without `dateRange`/`granularity`, then remove empty fields. |
| `remove_empty_query_fields` | `(query)` → *dict* | Strip empty `measures`/`dimensions`/`segments`/`timeDimensions`/`filters`/`order`. |
| `are_queries_equal` | `(query1, query2)` → *bool* | Compare two queries, order-sensitive on `order`. |

---

## Transports

### `HttpTransport`

> **HttpTransport**(`*`, api_url: `str`, authorization=None, method=None, headers=None, credentials=None, fetch_timeout=None, client: `Optional[httpx.Client]` = None)

Default synchronous transport. Preserves the JS behavior: JWT in `Authorization` **without**
`Bearer`, GET when the URL is under 2000 characters else POST, object params JSON-stringified
into the query string, and `x-request-id: {baseRequestId}-span-{n}`.

| Method | Signature |
| --- | --- |
| `request` | `(api_method: str, params: Mapping[str, Any])` → *[RawResponse](#rawresponse)* |
| `request_stream` | `(api_method: str, *, params, http_method="POST", fetch_timeout=None, base_request_id=None)` → *Iterator[bytes]* |

### `AsyncHttpTransport`

Same constructor and methods, backed by `httpx.AsyncClient`; `request` is a coroutine and
`request_stream` returns an `AsyncIterator[bytes]`.

### Transport protocols

`Transport` / `AsyncTransport` are `Protocol`s: an `authorization` attribute, a `request`
method, and an **optional** `request_stream`. A transport without `request_stream` works
normally; only `cube_sql_stream` raises `RuntimeError("Transport does not support streaming")`.

### `RawResponse`

> **RawResponse**(status: `Optional[int]` = None, text: `Optional[str]` = None, error: `Optional[str]` = None)

What a transport returns: an HTTP `status` + `text`, or a transport-level `error`
(`"timeout"` / `"network Error"`).

---

## Errors

```
CubeError
├── RequestError      (message, response, status)
├── CubeSqlError
└── MutexChangedError (unused — see below)
```

| Error | Raised when |
| --- | --- |
| `CubeError` | Base class for all SDK errors. |
| `RequestError` | Non-200 response, or an exhausted transport failure. Carries `.response` and `.status`. |
| `CubeSqlError` | A CubeSQL response is malformed, or an error chunk follows the schema. |
| `MutexChangedError` | Never raised — kept only so the JS error name resolves. See [differences](#differences-from-the-js-sdk). |

---

## Types

### `PivotConfig` (dict shape)

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `x` | `list[str]` | ✅ | Members on the x axis. `"measures"` is allowed. |
| `y` | `list[str]` | ✅ | Members on the y axis. `"measures"` is allowed. |
| `fillMissingDates` | `bool` | ✅ | Insert rows for gaps in a time series. |
| `joinDateRange` | `bool` | ✅ | Join the date range into a single x value. |
| `fillWithValue` | `Any` | ✅ | Value used for gaps (default `0` in `chart_pivot`). |
| `aliasSeries` | `list[str]` | ✅ | Aliases disambiguating duplicate measures when blending. |

### `TableColumn`

| Name | Type | Description |
| --- | --- | --- |
| `key` | `str` | Member key. |
| `dataIndex` | `str` | Key to read from a `table_pivot` row. |
| `title` / `shortTitle` | `str` | Display titles. |
| `type` | `str` | `"number"`, `"string"`, `"time"`, … |
| `format` / `meta` / `currency` / `granularity` | `Any` | Annotation passthrough (`None` when absent). |

### `CubeSqlResult`

| Name | Type | Optional? | Description |
| --- | --- | --- | --- |
| `schema` | `list[dict]` | | Columns, each `{"name": str, "column_type": str}`. |
| `data` | `list[list]` | | Row tuples. |
| `lastRefreshTime` | `str` | ✅ | Present only when the server reports it. |

### `CubeSqlStreamChunk`

Yielded by `cube_sql_stream`. One of:

| `type` | Fields |
| --- | --- |
| `"schema"` | `schema: list[dict]`, plus `lastRefreshTime: str` when present |
| `"data"` | `data: list[list]` |
| `"error"` | `error: str` |

Errors arrive as chunks rather than exceptions, so a stream can report a mid-result failure
without aborting iteration.

---

## Differences from the JS SDK

### Python-only additions

- **pandas layer** — `ResultSet.to_pandas()` and `.df`.
- **Fluent builders** — [`Query`](#query) and [`PivotConfig`](#pivotconfig) (immutable).
- **Operator filter DSL** — [`dim`/`measure`](#dim--measure) with `==`, `>=`, `&`, `|`.
- **Both sync and async clients** sharing one transform core.

### Behavioral divergences

- **Naming** is `snake_case` (`table_pivot`, `chart_pivot`, `drill_down`). Wire-format dict
  keys stay camelCase (`xValues`, `fillMissingDates`, `lastRefreshTime`).
- **`subscribe()` uses native cancellation** — a `threading.Event` (sync) or task cancellation
  (async) — instead of the JS `mutexObj`/`mutexKey` shared-dict supersession, which exists in
  JS only because it lacks a cancellation primitive. `MutexChangedError` is therefore never
  raised.
- **`subscribe()` always polls.** The JS transport can push (WebSocket); this port ships only
  HTTP, so it uses the same degraded polling path JS falls back to.
- **`ResultSet` methods take plain dicts** for `pivot_config`, never a `PivotConfig` object
  (passing one raises `TypeError` telling you to call `.build()`). Only `to_pandas()` accepts
  the builder.
- **Transport timeouts are broader.** Any transport-level failure counts against
  `network_error_retries`; JS retries only a literal `"network error"` and lets timeouts throw.
- **CubeSQL `timeout`/`aborted` sentinels** are handled by the polling loop (raising
  `RequestError`) before the response parser runs, so those JS branches don't exist here.

### Not ported

| Item | Reason |
| --- | --- |
| `format.ts` (d3 number/time formatting) | Not exported by the JS `index.ts` either; the server returns `formatDescription`. |
| `defaultHeuristics`, `movePivotItem`, `moveItemInArray`, `getOrderMembersFromOrder` | Playground/UI helpers — out of scope for a data SDK. |
| `defaultOrder`, `flattenFilters`, `getQueryMembers`, `isQueryPresent` | Small standalone helpers; not required by anything ported. |
| WebSocket transport | Not part of the JS `core` package either. |
