"""Fluent Query builder. `.build()` lowers to the same dict shape the Cube API
expects (mirroring src/types.ts `Query`), so it's interchangeable with a plain
dict wherever the client accepts a query."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

QueryLike = Union["Query", Mapping[str, Any]]


def _flatten(args: Sequence[Any]) -> list:
    result: list = []
    for a in args:
        if isinstance(a, (list, tuple)):
            result.extend(a)
        else:
            result.append(a)
    return result


@dataclass(frozen=True)
class Query:
    _measures: Tuple[str, ...] = ()
    _dimensions: Tuple[str, ...] = ()
    _segments: Tuple[str, ...] = ()
    _time_dimensions: Tuple[dict, ...] = ()
    _filters: Tuple[dict, ...] = ()
    _order: Tuple[Tuple[str, str], ...] = ()
    _limit: Optional[int] = None
    _offset: Optional[int] = None
    _timezone: Optional[str] = None
    _total: Optional[bool] = None

    def measures(self, *names: Union[str, Iterable[str]]) -> "Query":
        return replace(self, _measures=self._measures + tuple(_flatten(names)))

    def dimensions(self, *names: Union[str, Iterable[str]]) -> "Query":
        return replace(self, _dimensions=self._dimensions + tuple(_flatten(names)))

    def segments(self, *names: Union[str, Iterable[str]]) -> "Query":
        return replace(self, _segments=self._segments + tuple(_flatten(names)))

    def time_dimension(
        self,
        dimension: str,
        granularity: Optional[str] = None,
        date_range: Optional[Union[str, Sequence[str]]] = None,
    ) -> "Query":
        td: dict = {"dimension": dimension}
        if granularity is not None:
            td["granularity"] = granularity
        if date_range is not None:
            td["dateRange"] = list(date_range) if isinstance(date_range, (list, tuple)) else date_range
        return replace(self, _time_dimensions=self._time_dimensions + (td,))

    def filter(self, *filters: Mapping[str, Any]) -> "Query":
        return replace(self, _filters=self._filters + tuple(dict(f) for f in filters))

    def order(self, member: str, direction: str = "asc") -> "Query":
        return replace(self, _order=self._order + ((member, direction),))

    def limit(self, n: int) -> "Query":
        return replace(self, _limit=n)

    def offset(self, n: int) -> "Query":
        return replace(self, _offset=n)

    def timezone(self, tz: str) -> "Query":
        return replace(self, _timezone=tz)

    def total(self, flag: bool = True) -> "Query":
        return replace(self, _total=flag)

    def build(self) -> dict:
        q: dict = {}
        if self._measures:
            q["measures"] = list(self._measures)
        if self._dimensions:
            q["dimensions"] = list(self._dimensions)
        if self._segments:
            q["segments"] = list(self._segments)
        if self._time_dimensions:
            q["timeDimensions"] = list(self._time_dimensions)
        if self._filters:
            q["filters"] = list(self._filters)
        if self._order:
            q["order"] = [[member, direction] for member, direction in self._order]
        if self._limit is not None:
            q["limit"] = self._limit
        if self._offset is not None:
            q["offset"] = self._offset
        if self._timezone is not None:
            q["timezone"] = self._timezone
        if self._total is not None:
            q["total"] = self._total
        return q


def to_query_dict(query: QueryLike) -> dict:
    if isinstance(query, Query):
        return query.build()
    return dict(query)
