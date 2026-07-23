# Noridoc: query

Path: @/src/cubejs_client/query

### Overview
- The Pythonic query-building layer: a fluent `Query` builder and an operator-overloaded filter DSL (`dim("Users.age") >= 21`), plus query normalization/validation helpers.
- Everything here lowers to the same plain dict shape the Cube REST API and the JS SDK expect — a `Query` is a convenience for building that dict, never a replacement for it. Plain dict queries are always accepted alongside it.

### How it fits into the larger codebase
- `client/sync_client.py` (@/src/cubejs_client/client/docs.md) calls `to_query_dict()` on whatever the caller passed to `load()`/`sql()`/`dry_run()` before sending it over the wire — this is the layer's only external caller.
- Does not depend on `core/`, `transport/`, or `client/`; a `Query`/`Filter` can be constructed and inspected with no other part of the package involved.

### Core Implementation
- `model.py` (`Query`): an immutable `dataclasses.dataclass(frozen=True)` builder — every fluent method (`.measures()`, `.dimensions()`, `.filter()`, `.order()`, etc.) returns a *new* `Query` via `dataclasses.replace()` rather than mutating in place, so intermediate builder states can be freely reused/branched. `.build()` produces the final query dict; `to_query_dict()` accepts either a `Query` or a plain `Mapping` and normalizes both to a dict, which is what `CubeClient` methods actually consume.
- `builder.py` (`Member`, `Filter`, `dim()`/`measure()`): `dim("x")` returns a `Member`, whose comparison operators (`==`, `!=`, `>=`, etc.) are overloaded to *build* a `Filter` dict rather than perform a real comparison — deliberately mirroring SQLAlchemy `Column`-style query DSLs. `Filter` is a `dict` subclass whose `&`/`|` operators combine filters into `{"and": [...]}`/`{"or": [...]}` groups. Because `__eq__` is overloaded to return a `Filter` instead of a bool, `Member.__hash__` is explicitly set to `None` — `Member` instances are intentionally unhashable/uncomparable-for-equality outside this DSL.
- `validate.py`: `remove_empty_query_fields`, `validate_query` (drops filters missing `operator` and time dimensions with neither `dateRange` nor `granularity`), and `are_queries_equal`, ported from the non-UI parts of `utils.ts`.

### Things to Know
- `validate.py` deliberately does **not** port `defaultHeuristics`/`movePivotItem`/`getOrderMembersFromOrder` from the JS SDK's `utils.ts` — those are React-playground/UI helpers with no place in a headless data SDK. This is a YAGNI scope decision, not an oversight.
- `Filter` values are stringified (`_stringify`) when building filter dicts, matching the Cube API's expectation that filter `values` are strings even for numeric/date comparisons.

Created and maintained by Nori.
