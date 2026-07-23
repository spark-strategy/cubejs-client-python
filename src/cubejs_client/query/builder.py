"""Operator-overloaded filter DSL: `dim("Users.age") >= 21`, `dim(...).contains(...)`,
combined with `&`/`|` into `and`/`or` filter groups.

This is the Pythonic layer described in the project plan; it lowers to the
same filter dicts the Cube API expects (`{"member": ..., "operator": ..., "values": [...]}`),
so it coexists with plain dict queries via one shared validator
(`cubejs_client.query.validate`).
"""

from __future__ import annotations

from typing import Any


class Filter(dict):
    def __and__(self, other: "Filter") -> "Filter":
        return Filter({"and": [dict(self), dict(other)]})

    def __or__(self, other: "Filter") -> "Filter":  # type: ignore[override]
        return Filter({"or": [dict(self), dict(other)]})


def _stringify_value(v: Any) -> str:
    # bool is a subclass of int in Python, so this check must come before any
    # numeric handling: str(True) is "True", but the Cube API wire format (and
    # the JS SDK's own `value.toString()` convention) expects lowercase "true".
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _stringify(values) -> list:
    return [_stringify_value(v) for v in values]


class Member:
    """A dimension/measure reference. Comparison operators build `Filter` dicts
    rather than performing a real comparison — mirrors query-builder DSLs like
    SQLAlchemy's `Column`."""

    def __init__(self, name: str):
        self.name = name

    def _filter(self, operator: str, values=None) -> Filter:
        f: dict = {"member": self.name, "operator": operator}
        if values is not None:
            f["values"] = _stringify(values)
        return Filter(f)

    def __eq__(self, other: Any) -> Filter:  # type: ignore[override]
        # `dim("x") == None` almost always means "no value", not the literal
        # string "None" — route it to the `notSet` operator instead of
        # silently building a filter that can never match anything.
        if other is None:
            return self.is_not_set()
        return self._filter("equals", [other])

    def __ne__(self, other: Any) -> Filter:  # type: ignore[override]
        if other is None:
            return self.is_set()
        return self._filter("notEquals", [other])

    def __gt__(self, other: Any) -> Filter:
        return self._filter("gt", [other])

    def __ge__(self, other: Any) -> Filter:
        return self._filter("gte", [other])

    def __lt__(self, other: Any) -> Filter:
        return self._filter("lt", [other])

    def __le__(self, other: Any) -> Filter:
        return self._filter("lte", [other])

    def is_in(self, *values: Any) -> Filter:
        return self._filter("equals", values)

    def not_in(self, *values: Any) -> Filter:
        return self._filter("notEquals", values)

    def contains(self, *values: Any) -> Filter:
        return self._filter("contains", values)

    def not_contains(self, *values: Any) -> Filter:
        return self._filter("notContains", values)

    def starts_with(self, *values: Any) -> Filter:
        return self._filter("startsWith", values)

    def not_starts_with(self, *values: Any) -> Filter:
        return self._filter("notStartsWith", values)

    def ends_with(self, *values: Any) -> Filter:
        return self._filter("endsWith", values)

    def not_ends_with(self, *values: Any) -> Filter:
        return self._filter("notEndsWith", values)

    def is_set(self) -> Filter:
        return Filter({"member": self.name, "operator": "set"})

    def is_not_set(self) -> Filter:
        return Filter({"member": self.name, "operator": "notSet"})

    def in_date_range(self, start: Any, end: Any) -> Filter:
        return self._filter("inDateRange", [start, end])

    def not_in_date_range(self, start: Any, end: Any) -> Filter:
        return self._filter("notInDateRange", [start, end])

    def before_date(self, value: Any) -> Filter:
        return self._filter("beforeDate", [value])

    def before_or_on_date(self, value: Any) -> Filter:
        return self._filter("beforeOrOnDate", [value])

    def after_date(self, value: Any) -> Filter:
        return self._filter("afterDate", [value])

    def after_or_on_date(self, value: Any) -> Filter:
        return self._filter("afterOrOnDate", [value])

    __hash__ = None  # type: ignore[assignment]


def dim(name: str) -> Member:
    return Member(name)


def measure(name: str) -> Member:
    return Member(name)
