"""Port of the JS SDK's src/time.ts (predefined-granularity subset).

The JS implementation builds time-series axes with dayjs, using a custom
locale where the week starts on Monday, and formats every point as a naive
wall-clock string (no timezone, millisecond precision). This module
reproduces that exact boundary arithmetic with `datetime` + `dateutil`
instead of delegating to `pandas.date_range`/`resample`, whose default
week/period-boundary semantics differ (week-ending-Sunday, etc).

Custom (PostgreSQL-interval-style) granularities are not implemented yet —
that's deferred to a later phase; `ResultSet.time_series` raises
`NotImplementedError` for any granularity outside `TIME_SERIES`.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Callable

from dateutil.relativedelta import relativedelta

DateRegex = re.compile(r"^\d\d\d\d-\d\d-\d\d$")
LocalDateRegex = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z?$")

_ISO_RE = re.compile(
    r"^(?P<y>\d{4})-(?P<mo>\d{2})-(?P<d>\d{2})"
    r"(?:[T ](?P<h>\d{2}):(?P<mi>\d{2})(?::(?P<s>\d{2})(?:\.(?P<ms>\d+))?)?)?"
)

_UNIT_ALIASES = {
    "d": "day",
    "M": "month",
    "y": "year",
    "h": "hour",
    "m": "minute",
    "s": "second",
    "w": "week",
    "day": "day",
    "month": "month",
    "year": "year",
    "hour": "hour",
    "minute": "minute",
    "second": "second",
    "week": "week",
    "quarter": "quarter",
}

_RELATIVEDELTA_KEY = {
    "year": "years",
    "month": "months",
    "week": "weeks",
    "day": "days",
    "hour": "hours",
    "minute": "minutes",
    "second": "seconds",
}


def parse_datetime(value: "str | dt.datetime") -> dt.datetime:
    """Parse an ISO-ish date/datetime string as a naive wall-clock datetime,
    ignoring any trailing 'Z'/offset (mirrors the SDK's naive-datetime policy)."""
    if isinstance(value, dt.datetime):
        return value.replace(tzinfo=None)
    match = _ISO_RE.match(str(value))
    if not match:
        raise ValueError(f"Unrecognized date string: {value!r}")
    ms = (match.group("ms") or "0").ljust(6, "0")[:6]
    return dt.datetime(
        int(match["y"]),
        int(match["mo"]),
        int(match["d"]),
        int(match["h"] or 0),
        int(match["mi"] or 0),
        int(match["s"] or 0),
        int(ms),
    )


def _resolve_unit(unit: str) -> str:
    resolved = _UNIT_ALIASES.get(unit)
    if resolved is None:
        raise ValueError(f"Unknown time unit: {unit!r}")
    return resolved


def _start_of(d: dt.datetime, unit: str) -> dt.datetime:
    unit = _resolve_unit(unit)
    if unit == "year":
        return d.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    if unit == "quarter":
        quarter_month = ((d.month - 1) // 3) * 3 + 1
        return d.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    if unit == "month":
        return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if unit == "week":
        delta_days = d.isoweekday() - 1  # Monday-start week
        start = d - dt.timedelta(days=delta_days)
        return start.replace(hour=0, minute=0, second=0, microsecond=0)
    if unit == "day":
        return d.replace(hour=0, minute=0, second=0, microsecond=0)
    if unit == "hour":
        return d.replace(minute=0, second=0, microsecond=0)
    if unit == "minute":
        return d.replace(second=0, microsecond=0)
    if unit == "second":
        return d.replace(microsecond=0)
    raise ValueError(f"Unknown time unit: {unit!r}")


def _add(d: dt.datetime, n: int, unit: str) -> dt.datetime:
    unit = _resolve_unit(unit)
    if unit == "quarter":
        return d + relativedelta(months=3 * n)
    return d + relativedelta(**{_RELATIVEDELTA_KEY[unit]: n})


def _end_of(d: dt.datetime, unit: str) -> dt.datetime:
    start = _start_of(d, unit)
    return _add(start, 1, unit) - dt.timedelta(milliseconds=1)


class DayRange:
    def __init__(self, start: dt.datetime, end: dt.datetime):
        self.start = start
        self.end = end

    def by(self, unit: str) -> list:
        resolved = _resolve_unit(unit)
        results = []
        cur = self.start
        while _start_of(cur, resolved) < self.end or cur == self.end:
            results.append(cur)
            cur = _add(cur, 1, resolved)
        return results

    def snap_to(self, unit: str) -> "DayRange":
        resolved = _resolve_unit(unit)
        return DayRange(_start_of(self.start, resolved), _end_of(self.end, resolved))


def day_range(from_: "str | dt.datetime", to_: "str | dt.datetime") -> DayRange:
    return DayRange(parse_datetime(from_), parse_datetime(to_))


def _ts_day(r: DayRange) -> list:
    return [d.strftime("%Y-%m-%dT00:00:00.000") for d in r.by("day")]


def _ts_month(r: DayRange) -> list:
    snapped = r.snap_to("month")
    return [d.strftime("%Y-%m-01T00:00:00.000") for d in snapped.by("month")]


def _ts_year(r: DayRange) -> list:
    snapped = r.snap_to("year")
    return [d.strftime("%Y-01-01T00:00:00.000") for d in snapped.by("year")]


def _ts_hour(r: DayRange) -> list:
    return [d.strftime("%Y-%m-%dT%H:00:00.000") for d in r.by("hour")]


def _ts_minute(r: DayRange) -> list:
    return [d.strftime("%Y-%m-%dT%H:%M:00.000") for d in r.by("minute")]


def _ts_second(r: DayRange) -> list:
    return [d.strftime("%Y-%m-%dT%H:%M:%S.000") for d in r.by("second")]


def _ts_week(r: DayRange) -> list:
    snapped = r.snap_to("week")
    return [_start_of(d, "week").strftime("%Y-%m-%dT00:00:00.000") for d in snapped.by("week")]


def _ts_quarter(r: DayRange) -> list:
    snapped = r.snap_to("quarter")
    return [_start_of(d, "quarter").strftime("%Y-%m-%dT00:00:00.000") for d in snapped.by("quarter")]


TIME_SERIES: "dict[str, Callable[[DayRange], list]]" = {
    "day": _ts_day,
    "month": _ts_month,
    "year": _ts_year,
    "hour": _ts_hour,
    "minute": _ts_minute,
    "second": _ts_second,
    "week": _ts_week,
    "quarter": _ts_quarter,
}


def is_predefined_granularity(granularity: str) -> bool:
    return granularity in TIME_SERIES
