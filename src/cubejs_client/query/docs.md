# Noridoc: query

Path: @/src/cubejs_client/query

### Overview
- The Pythonic query-building layer: a fluent `Query` builder, a `PivotConfig` builder, and an operator-overloaded filter DSL (`dim("Users.age") >= 21`), plus query normalization/validation helpers.
- Everything here lowers to the same plain dict shape the Cube REST API / the JS SDK expect, and that @/src/cubejs_client/core/docs.md consumes — a `Query`/`PivotConfig` is a convenience for building that dict, never a replacement for it. Plain dicts are always accepted alongside them.

### How it fits into the larger codebase
- `client/sync_client.py`/`client/async_client.py` (@/src/cubejs_client/client/docs.md) call `to_query_dict()` on whatever the caller passed to `load()`/`sql()`/`dry_run()` before sending it over the wire.
- `results/pandas_adapter.py` (@/src/cubejs_client/results/docs.md) is the only place that accepts a `PivotConfig` instance directly (via `to_pivot_config_dict()`) and lowers it to a dict before handing it to `core/result_set.py`'s `ResultSet` methods, which take plain dicts only.
- Does not depend on `core/`, `transport/`, or `client/`; a `Query`/`PivotConfig`/`Filter` can be constructed and inspected with no other part of the package involved.

### Core Implementation
- `model.py` (`Query`): an immutable `dataclasses.dataclass(frozen=True)` builder — every fluent method (`.measures()`, `.dimensions()`, `.filter()`, `.order()`, etc.) returns a *new* `Query` via `dataclasses.replace()` rather than mutating in place, so intermediate builder states can be freely reused/branched. `.build()` produces the final query dict; `to_query_dict()` accepts either a `Query` or a plain `Mapping` and normalizes both to a dict, which is what `CubeClient`/`AsyncCubeClient` methods actually consume.
- `pivot_config.py` (`PivotConfig`): the same immutable-builder pattern as `Query`, over `pivotConfig`'s shape instead (`.x()`, `.y()`, `.fill_missing_dates()`, `.join_date_range()`, `.fill_with_value()`, `.alias_series()`, `.build()`). `to_pivot_config_dict()` accepts a `PivotConfig`, a plain dict, or `None`, normalizing to a dict/`None`. An explicitly-built `PivotConfig()` (even with no fields set) always lowers to `{}`, never to `None` — mirroring JS's `pivotConfig || {defaultXY...}`, where any truthy `pivotConfig` (including `{}`) skips the x/y smart default in @/src/cubejs_client/core/docs.md's `get_normalized_pivot_config`; pass `None` itself to opt into that default.
- `builder.py` (`Member`, `Filter`, `dim()`/`measure()`): `dim("x")` returns a `Member`, whose comparison operators (`==`, `!=`, `>=`, etc.) are overloaded to *build* a `Filter` dict rather than perform a real comparison — deliberately mirroring SQLAlchemy `Column`-style query DSLs. `Filter` is a `dict` subclass whose `&`/`|` operators combine filters into `{"and": [...]}`/`{"or": [...]}` groups. Because `__eq__` is overloaded to return a `Filter` instead of a bool, `Member.__hash__` is explicitly set to `None` — `Member` instances are intentionally unhashable/uncomparable-for-equality outside this DSL.
- `validate.py`: `remove_empty_query_fields`, `validate_query` (drops filters missing `operator` and time dimensions with neither `dateRange` nor `granularity`), and `are_queries_equal`, ported from the non-UI parts of `utils.ts`.

### Things to Know
- `validate.py` deliberately does **not** port `defaultHeuristics`/`movePivotItem`/`getOrderMembersFromOrder` from the JS SDK's `utils.ts` — those are React-playground/UI helpers with no place in a headless data SDK. This is a YAGNI scope decision, not an oversight.
- `Filter` values are stringified (`_stringify`) when building filter dicts, matching the Cube API's expectation that filter `values` are strings even for numeric/date comparisons.
- `PivotConfig` is deliberately *not* accepted by `core/result_set.py`'s own methods (`pivot`, `chart_pivot`, `table_pivot`, `table_columns`, `series`, `series_names`) — passing one there raises a `TypeError` telling the caller to call `.build()` first, keeping `core/` a plain-dict-only, JS-behavior-faithful layer.

Created and maintained by Nori.
