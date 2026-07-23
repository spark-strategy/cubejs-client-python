"""Pandas convenience layer on top of the faithful ResultSet core.

`core.result_set` stays pandas-free (so the golden-tested core has no hard
pandas dependency); this module builds `to_dataframe`/`.to_pandas()`/`.df` on
top of its already-correct `table_pivot`/`chart_pivot` output, so DataFrame
correctness reduces to core correctness. Importing this module attaches
`to_pandas`/`df` onto `ResultSet` (pandas is a required dependency of this
package, so `cubejs_client/__init__.py` always imports it).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from ..core.result_set import ResultSet


def _flatten_columns(columns: list) -> list:
    flat = []
    for column in columns:
        if column.get("children"):
            flat.extend(_flatten_columns(column["children"]))
        else:
            flat.append(column)
    return flat


def to_dataframe(result_set: ResultSet, pivot_config: Optional[dict] = None, kind: str = "table") -> pd.DataFrame:
    if kind == "table":
        rows = result_set.table_pivot(pivot_config)
        columns = _flatten_columns(result_set.table_columns(pivot_config))
        df = pd.DataFrame.from_records(rows)

        ordered = [c["dataIndex"] for c in columns if c["dataIndex"] in df.columns]
        if ordered:
            df = df[ordered]

        # table_pivot() stays byte-for-byte faithful to the JS SDK (raw string
        # measure values, no coercion); dtype casting is this convenience
        # layer's job, driven by table_columns()' `type` metadata.
        for column in columns:
            key = column["dataIndex"]
            if key not in df.columns:
                continue
            try:
                if column.get("type") == "number":
                    df[key] = pd.to_numeric(df[key])
                elif column.get("type") == "time":
                    df[key] = pd.to_datetime(df[key])
            except (ValueError, TypeError):
                pass

        return df

    if kind == "chart":
        # chart_pivot() already applies JS-parseFloat-style numeric coercion,
        # so no further casting is needed here.
        return pd.DataFrame.from_records(result_set.chart_pivot(pivot_config))

    raise ValueError(f"Unknown kind: {kind!r} (expected 'table' or 'chart')")


def _to_pandas(self: ResultSet, pivot_config: Optional[dict] = None, kind: str = "table") -> pd.DataFrame:
    return to_dataframe(self, pivot_config=pivot_config, kind=kind)


def _df(self: ResultSet) -> pd.DataFrame:
    return to_dataframe(self)


ResultSet.to_pandas = _to_pandas  # type: ignore[attr-defined]
ResultSet.df = property(_df)  # type: ignore[attr-defined]
