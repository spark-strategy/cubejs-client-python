"""Port of the JS SDK's src/time.ts, including custom (PostgreSQL-interval-
style) granularities.

The JS implementation builds time-series axes with dayjs, using a custom
locale where the week starts on Monday, and formats every point as a naive
wall-clock string (no timezone, millisecond precision). This module
reproduces that exact boundary arithmetic with `datetime` + `dateutil`
instead of delegating to `pandas.date_range`/`resample`, whose default
week/period-boundary semantics differ (week-ending-Sunday, etc).

Custom granularities (e.g. `interval: '2 months 3 weeks'`) are resolved via
`parse_sql_interval`/`add_interval`/`subtract_interval`/`align_to_origin`/
`time_series_from_custom_interval`, ported from the matching functions in
time.ts. `DayRange.snap_to` also has a custom-granularity branch (used by
`ResultSet.drill_down`), which needs the `annotations` mapping to look up a
custom granularity's interval/origin/offset metadata by dimension+name.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Callable, Mapping, Optional

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


def parse_datetime(value: "str | dt.datetime | None") -> dt.datetime:
    """Parse an ISO-ish date/datetime string as a naive wall-clock datetime,
    ignoring any trailing 'Z'/offset (mirrors the SDK's naive-datetime policy).

    `None` (missing xValue/yValue in `ResultSet.drill_down`, e.g.) resolves to
    the current moment, mirroring JS `dayjs(undefined)` — dayjs treats a
    missing argument as "now" rather than an error, and `drillDown` relies on
    that for a member with a time granularity but no corresponding drilled
    value."""
    if value is None:
        return _now()
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


def _now() -> dt.datetime:
    """Current moment, used wherever JS falls back to `internalDayjs()` with
    no argument (a custom granularity's `offset` with no explicit `origin`;
    `parse_datetime(None)`).

    Only provably non-flaky for interval lengths that evenly divide a
    calendar year (e.g. a whole-year interval always aligns to the same
    month/day regardless of which year `_now()` falls in — see
    test_time_series_golden.py's `test_one_year_with_offset_2_months_no_origin`
    for the full argument). For other interval lengths (e.g. "5 months", or
    anything that crosses a leap day inconsistently), the computed origin —
    and therefore every bucket boundary — genuinely depends on the current
    date and can differ between runs. Monkeypatch this function directly if a
    test needs deterministic output for such a case.
    """
    return dt.datetime.now()


def parse_sql_interval(interval_str: str) -> "dict[str, int]":
    """Port of parseSqlInterval (time.ts:101-115): 'X unit Y unit ...' -> {unit: N},
    singularizing each unit ('months' -> 'month')."""
    interval: "dict[str, int]" = {}
    parts = interval_str.split()
    for i in range(0, len(parts), 2):
        value = int(parts[i])
        unit = parts[i + 1]
        singular_unit = unit[:-1] if unit.endswith("s") else unit
        interval[singular_unit] = value
    return interval


def add_interval(date: dt.datetime, interval: "dict[str, int]") -> dt.datetime:
    result = date
    for unit, value in interval.items():
        result = _add(result, value, unit)
    return result


def subtract_interval(date: dt.datetime, interval: "dict[str, int]") -> dt.datetime:
    result = date
    for unit, value in interval.items():
        result = _add(result, -value, unit)
    return result


def align_to_origin(start_date: dt.datetime, interval: "dict[str, int]", origin: dt.datetime) -> dt.datetime:
    """Port of alignToOrigin (time.ts:158-193): the closest bucket boundary
    at-or-before `start_date`, aligned to `origin`, stepping by `interval`."""
    aligned_date = start_date

    offset_date = add_interval(origin, interval)
    is_interval_negative = offset_date < origin
    offset_date = origin

    if start_date < origin:
        interval_op = add_interval if is_interval_negative else subtract_interval
        while offset_date > start_date:
            offset_date = interval_op(offset_date, interval)
        aligned_date = offset_date
    else:
        interval_op = subtract_interval if is_interval_negative else add_interval
        while offset_date < start_date:
            aligned_date = offset_date
            offset_date = interval_op(offset_date, interval)
        if offset_date == start_date:
            aligned_date = offset_date

    return aligned_date


def time_series_from_custom_interval(from_: "str | dt.datetime", to_: "str | dt.datetime", granularity: dict) -> list:
    """Port of timeSeriesFromCustomInterval (time.ts:264-282)."""
    interval_parsed = parse_sql_interval(granularity["interval"])
    start = parse_datetime(from_)
    end = parse_datetime(to_)

    origin = parse_datetime(granularity["origin"]) if granularity.get("origin") else _start_of(_now(), "year")
    if granularity.get("offset"):
        origin = add_interval(origin, parse_sql_interval(granularity["offset"]))

    aligned_start = align_to_origin(start, interval_parsed, origin)

    dates = []
    while aligned_start < end or aligned_start == end:
        dates.append(aligned_start.strftime("%Y-%m-%dT%H:%M:%S.000"))
        aligned_start = add_interval(aligned_start, interval_parsed)
    return dates


class DayRange:
    def __init__(self, start: dt.datetime, end: dt.datetime, annotations: Optional[Mapping[str, Any]] = None):
        self.start = start
        self.end = end
        self.annotations = annotations

    def by(self, unit: str) -> list:
        resolved = _resolve_unit(unit)
        results = []
        cur = self.start
        while _start_of(cur, resolved) < self.end or cur == self.end:
            results.append(cur)
            cur = _add(cur, 1, resolved)
        return results

    def snap_to(self, unit: str) -> "DayRange":
        if not is_predefined_granularity(unit) and self.annotations:
            custom_granularity = None
            for key, annotation in self.annotations.items():
                if key.endswith(f".{unit}") and annotation.get("granularity"):
                    custom_granularity = annotation["granularity"]
                    break

            if custom_granularity and custom_granularity.get("interval"):
                interval_parsed = parse_sql_interval(custom_granularity["interval"])
                interval_start = self.start

                if custom_granularity.get("origin") or custom_granularity.get("offset"):
                    if custom_granularity.get("origin"):
                        origin = parse_datetime(custom_granularity["origin"])
                    else:
                        origin = add_interval(
                            _start_of(_now(), "year"), parse_sql_interval(custom_granularity["offset"])
                        )
                    interval_start = align_to_origin(interval_start, interval_parsed, origin)

                interval_end = add_interval(interval_start, interval_parsed) - dt.timedelta(milliseconds=1)
                return DayRange(interval_start, interval_end, self.annotations)

        resolved = _resolve_unit(unit)
        return DayRange(_start_of(self.start, resolved), _end_of(self.end, resolved), self.annotations)


def day_range(
    from_: "str | dt.datetime", to_: "str | dt.datetime", annotations: Optional[Mapping[str, Any]] = None
) -> DayRange:
    return DayRange(parse_datetime(from_), parse_datetime(to_), annotations)


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
