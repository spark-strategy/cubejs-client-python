"""Golden tests ported from ResultSet.test.ts describe('timeSeries') (lines ~12-51)."""

from cubejs_client.core.result_set import ResultSet


def test_time_series_month_granularity():
    rs = ResultSet({})
    time_dimension = {
        "dateRange": ["2015-01-01", "2015-12-31"],
        "granularity": "month",
        "dimension": "Events.time",
    }

    assert rs.time_series(time_dimension) == [
        "2015-01-01T00:00:00.000",
        "2015-02-01T00:00:00.000",
        "2015-03-01T00:00:00.000",
        "2015-04-01T00:00:00.000",
        "2015-05-01T00:00:00.000",
        "2015-06-01T00:00:00.000",
        "2015-07-01T00:00:00.000",
        "2015-08-01T00:00:00.000",
        "2015-09-01T00:00:00.000",
        "2015-10-01T00:00:00.000",
        "2015-11-01T00:00:00.000",
        "2015-12-01T00:00:00.000",
    ]


def test_time_series_quarter_granularity():
    rs = ResultSet({})
    time_dimension = {
        "dateRange": ["2015-01-01", "2015-12-31"],
        "granularity": "quarter",
        "dimension": "Events.time",
    }

    assert rs.time_series(time_dimension) == [
        "2015-01-01T00:00:00.000",
        "2015-04-01T00:00:00.000",
        "2015-07-01T00:00:00.000",
        "2015-10-01T00:00:00.000",
    ]


def test_time_series_hour_granularity_full_day():
    rs = ResultSet({})
    time_dimension = {
        "dateRange": ["2015-01-01", "2015-01-01"],
        "granularity": "hour",
        "dimension": "Events.time",
    }

    assert rs.time_series(time_dimension) == [
        f"2015-01-01T{h:02d}:00:00.000" for h in range(24)
    ]


def test_time_series_hour_granularity_not_full_day():
    """Exercises the pad_to_day=False path: an explicit dateRange with a time
    component (not matched by DateRegex) must NOT be snapped to day boundaries."""
    rs = ResultSet({})
    time_dimension = {
        "dateRange": ["2015-01-01T10:30:00.000", "2015-01-01T13:59:00.000"],
        "granularity": "hour",
        "dimension": "Events.time",
    }

    assert rs.time_series(time_dimension) == [
        "2015-01-01T10:00:00.000",
        "2015-01-01T11:00:00.000",
        "2015-01-01T12:00:00.000",
        "2015-01-01T13:00:00.000",
    ]
