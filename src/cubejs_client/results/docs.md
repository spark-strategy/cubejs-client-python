# Noridoc: results

Path: @/src/cubejs_client/results

### Overview
- The pandas convenience layer: turns `ResultSet` output into `DataFrame`s. This is the module that makes pandas "the primary result type" for the package's Pythonic-first API, per the project's design goals.
- Deliberately kept separate from @/src/cubejs_client/core/docs.md, which stays pandas-free by design.

### How it fits into the larger codebase
- Consumes only the public `ResultSet` methods from @/src/cubejs_client/core/docs.md (`table_pivot()`, `table_columns()`, `chart_pivot()`) — it never reaches into `ResultSet` internals.
- `cubejs_client/__init__.py` (@/src/cubejs_client/docs.md) always imports this module (as `_pandas_adapter`, for its side effect) because pandas is a required dependency of the package, not an optional extra — so `to_pandas()`/`.df` are available on every `ResultSet` returned by `CubeClient.load()` (@/src/cubejs_client/client/docs.md) without the caller needing to import anything extra.

### Core Implementation
- `to_dataframe(result_set, pivot_config=None, kind="table")`: `pivot_config` accepts a plain dict, a @/src/cubejs_client/query/docs.md `PivotConfig` builder instance, or `None` — this is the *only* place in the package that accepts a `PivotConfig` directly, via `to_pivot_config_dict()`, which lowers it to a dict (or passes `None`/a dict through unchanged) before handing it to `ResultSet`'s own methods, which take plain dicts only. The rest of the conversion logic dispatches on `kind`:
  - `kind="table"` (default): builds a `DataFrame` from `table_pivot()` rows, reordered to match `table_columns()`'s flattened (nested columns flattened via `_flatten_columns`) `dataIndex` order, then applies dtype casting per-column based on `table_columns()`'s `type` metadata (`"number"` → `pd.to_numeric`, `"time"` → `pd.to_datetime`).
  - `kind="chart"`: builds a `DataFrame` directly from `chart_pivot()` rows with no further casting.
- `_to_pandas`/`_df` are thin wrappers around `to_dataframe()`, attached onto the `ResultSet` class at import time as `ResultSet.to_pandas` (method) and `ResultSet.df` (property, `kind="table"` only) via direct monkey-patching (`ResultSet.to_pandas = _to_pandas`).

### Things to Know
- `table_pivot()` itself stays byte-for-byte faithful to the JS SDK — raw string measure values, no numeric coercion. Dtype casting is entirely this module's responsibility, applied *after* the fact using `table_columns()`'s `type` field; this keeps `core/` free of any pandas-specific type-mapping logic.
- The per-column casting is wrapped in `try/except (ValueError, TypeError): pass` — this exists specifically because pandas 2.x removed the `errors="ignore"` parameter that `pd.to_numeric`/`pd.to_datetime` calls originally relied on to silently skip uncastable columns; the try/except reproduces that same "best-effort, leave as-is on failure" behavior.
- `chart_pivot()` does not need the same casting step because it already applies JS-`parseFloat`-style numeric coercion itself (see `core/js_compat.py`'s `js_parse_float`, used inside `ResultSet.chart_pivot`) — so `kind="chart"` DataFrames are built directly without a second casting pass.
- Because `ResultSet.to_pandas`/`.df` are attached via monkey-patching rather than being defined on the class itself, they only exist once `results.pandas_adapter` has been imported at least once in the process — relying on `core.result_set.ResultSet` directly (bypassing `cubejs_client/__init__.py`) without importing this module will not have `.to_pandas()`/`.df` available.

Created and maintained by Nori.
