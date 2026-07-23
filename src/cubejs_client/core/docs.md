# Noridoc: core

Path: @/src/cubejs_client/core

### Overview
- The "faithful port" layer: transport-free, pandas-free translations of the JS SDK's `ResultSet.ts`, `time.ts`, `Meta.ts`, `utils.ts`'s `aliasSeries`, and `CubeApi`'s response-shaping logic.
- Golden-tested against fixtures transcribed verbatim from the JS SDK's own test suite (@/tests/golden), so this layer's correctness is measured against real JS output, not against a from-scratch spec.
- Highest-risk code in the repo: `result_set.py`'s pivot engine is intricate, order-sensitive, and has already caught at least one real porting bug (see Things to Know).

### How it fits into the larger codebase
- `client/sync_client.py` (@/src/cubejs_client/client/docs.md) is the only external caller: it runs `decode_response_data()` on the raw HTTP response body, then constructs a `ResultSet` from it, and returns `Meta` from `meta()`.
- `results/pandas_adapter.py` (@/src/cubejs_client/results/docs.md) builds `DataFrame`s from `ResultSet.table_pivot()`/`table_columns()`/`chart_pivot()` output — it never reaches into `core/` internals directly.
- Nothing in `core/` imports `query/`, `transport/`, `client/`, or `results/` — dependencies only flow inward from those layers.

### Core Implementation
- `js_compat.py`: small functions reproducing specific JS runtime quirks (`Number.parseFloat`'s leading-numeric-prefix parsing, `Number()` coercion, `Array.prototype.join`'s null-to-empty-string behavior, ramda's `uniq` and `mergeDeepLeft`) that the rest of `core/` depends on to avoid silently diverging from JS output on the same input.
- `response_decode.py` (`decode_response_data`): mutates a raw load-response dict in place — applies numeric casting (`castNumerics`) and unpacks `compact`/`columnar` API response formats into the row-dict shape the rest of the pipeline expects, before a `ResultSet` is ever constructed.
- `pivot_config.py` (`get_normalized_pivot_config`): computes the effective `{x, y, fillMissingDates, joinDateRange, ...}` pivot configuration from a query and an optional caller-supplied `pivot_config`, including the "smart default" (x = time-dimension members, y = dimensions) applied when no config is given.
- `result_set.py` (`ResultSet`): the pivot engine. `pivot()` is the core algorithm everything else (`chart_pivot`, `table_pivot`, `table_columns`, `series`, `series_names`, `total_row`) builds on. `time_series.py` supplies the date-axis generation `pivot()` uses when `fillMissingDates` is set and the x-axis is a single time-dimension.
- `meta.py` (`Meta`): wraps a `meta` API response with member/operator lookups (`resolve_member`, `filter_operators_for_member`, `default_time_dimension_name_for`) used for building UIs/validating queries against a schema.
- `alias.py` (`alias_series`): builds display keys/labels for series, applying `pivotConfig.aliasSeries` overrides and de-duplicating measure names across blended queries.

### Things to Know
- **`pivot_config=None` vs `pivot_config={}` are not interchangeable.** JS's `pivotConfig || (...)` treats an explicit `{}` as truthy (so it does *not* trigger the smart default), but Python's `{} or ...` treats `{}` as falsy. `get_normalized_pivot_config` checks `pivot_config is None` explicitly to match JS. This is why `ResultSet.pivot()`/`chart_pivot()` pass `pivot_config` straight through (default `None`, so an un-called `pivot()` gets the smart default), while `table_pivot()`/`table_columns()` explicitly coerce `None` to `{}` before normalizing — mirroring the JS SDK's own inconsistency between these methods rather than "fixing" it.
- **JS out-of-bounds array access is reproduced, not avoided.** `_measure_from_axis` mirrors `axisValues[axisValues.length - 1]`, which is `undefined` (not a thrown error) when the array is empty in JS. The Python port returns `None` for an empty sequence instead of raising `IndexError`. This was a real bug caught by the golden tests during development, not a hypothetical edge case.
- Measure-value resolution in `pivot()` must distinguish "missing" (`None`, falls back to `fillWithValue` or `0`) from "present but falsy" (e.g. `0`) — the JS `!= null` check, not a truthiness check, is what `measure_value()` reproduces.
- `time_series.py` only implements the predefined granularities (`day/week/month/quarter/year/hour/minute/second`); it hand-rolls boundary arithmetic with `datetime` + `dateutil.relativedelta` rather than `pandas.date_range`/`resample` because pandas' default week/period boundaries (week ending Sunday) differ from the JS SDK's custom dayjs locale (week starting Monday) and its naive, timezone-free wall-clock string formatting. Any non-predefined ("custom", PostgreSQL-interval-style) granularity raises `NotImplementedError` from `ResultSet.time_series()` by design — deferred to a later phase.
- Multi-result `ResultSet`s (`len(self.load_responses) > 1`, i.e. `compareDateRangeQuery`/`blendingQuery`) are detected in `pivot()` and raise `NotImplementedError` rather than silently producing wrong output; `mergePivots`/`decompose` from the JS SDK are not ported yet.
- `serialize()`/`deserialize()` round-trip the raw `load_response` dict (deep-copied) so a `ResultSet` can be cached/transmitted and reconstructed without re-querying.

Created and maintained by Nori.
