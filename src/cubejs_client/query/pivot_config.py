"""Fluent PivotConfig builder, mirroring `Query` (src/types.ts `PivotConfig`).
`.build()` lowers to the same JS-camelCase dict shape
`core.pivot_config.get_normalized_pivot_config` expects.

Like `Query`, this is a Pythonic convenience over the faithful low-level
core: `ResultSet.pivot`/`chart_pivot`/`table_pivot`/`table_columns`/`series`/
`series_names` only accept plain dicts (call `.build()` first if you're
calling them directly — passing a `PivotConfig` raises a `TypeError` there).
`ResultSet.to_pandas(pivot_config=...)` (results/pandas_adapter.py) is the
one place that accepts a `PivotConfig` instance directly and converts it via
`to_pivot_config_dict`.

An explicitly-built `PivotConfig()` (even with no fields set) lowers to `{}`,
never to `None` — mirroring JS `pivotConfig || {defaultXY...}`, where any
truthy pivotConfig object (including `{}`) skips the x/y smart default.
Pass `None` itself (not a `PivotConfig`) to opt into the smart default.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

PivotConfigLike = Union["PivotConfig", Mapping[str, Any], None]


def _flatten(args: Sequence[Any]) -> list:
    result: list = []
    for a in args:
        if isinstance(a, (list, tuple)):
            result.extend(a)
        else:
            result.append(a)
    return result


@dataclass(frozen=True)
class PivotConfig:
    _x: Tuple[str, ...] = ()
    _y: Tuple[str, ...] = ()
    _fill_missing_dates: Optional[bool] = None
    _join_date_range: Optional[bool] = None
    _fill_with_value: Optional[Any] = None
    _alias_series: Tuple[str, ...] = ()

    def x(self, *members: Union[str, Iterable[str]]) -> "PivotConfig":
        return replace(self, _x=self._x + tuple(_flatten(members)))

    def y(self, *members: Union[str, Iterable[str]]) -> "PivotConfig":
        return replace(self, _y=self._y + tuple(_flatten(members)))

    def fill_missing_dates(self, flag: bool = True) -> "PivotConfig":
        return replace(self, _fill_missing_dates=flag)

    def join_date_range(self, flag: bool = True) -> "PivotConfig":
        return replace(self, _join_date_range=flag)

    def fill_with_value(self, value: Any) -> "PivotConfig":
        return replace(self, _fill_with_value=value)

    def alias_series(self, *names: Union[str, Iterable[str]]) -> "PivotConfig":
        return replace(self, _alias_series=self._alias_series + tuple(_flatten(names)))

    def build(self) -> dict:
        d: dict = {}
        if self._x:
            d["x"] = list(self._x)
        if self._y:
            d["y"] = list(self._y)
        if self._fill_missing_dates is not None:
            d["fillMissingDates"] = self._fill_missing_dates
        if self._join_date_range is not None:
            d["joinDateRange"] = self._join_date_range
        if self._fill_with_value is not None:
            d["fillWithValue"] = self._fill_with_value
        if self._alias_series:
            d["aliasSeries"] = list(self._alias_series)
        return d


def to_pivot_config_dict(pivot_config: PivotConfigLike) -> Optional[dict]:
    if pivot_config is None:
        return None
    if isinstance(pivot_config, PivotConfig):
        return pivot_config.build()
    return dict(pivot_config)
