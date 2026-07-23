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


class TestCustomGranularity:
    """Ported verbatim from ResultSet.test.ts describe('timeSeries') custom-
    interval cases (lines ~105-400)."""

    def test_one_year_with_origin_2020_01_01(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2023-12-31"], "granularity": "one_year", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.one_year": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "1 year", "title": "1 year", "interval": "1 year", "origin": "2020-01-01"},
                }
            },
        )

        assert result == ["2021-01-01T00:00:00.000", "2022-01-01T00:00:00.000", "2023-01-01T00:00:00.000"]

    def test_one_year_with_origin_2025_03_01(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2022-12-31"], "granularity": "one_year", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.one_year": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "1 year", "title": "1 year", "interval": "1 year", "origin": "2025-03-01"},
                }
            },
        )

        assert result == ["2020-03-01T00:00:00.000", "2021-03-01T00:00:00.000", "2022-03-01T00:00:00.000"]

    def test_one_year_with_offset_2_months_no_origin(self):
        """No JS test-run-time flakiness despite the default origin being
        derived from the current year: for a whole-year interval, only the
        origin's month/day (here, +2 months = March 1) determines the aligned
        bucket boundary, never the year — see time_series.py's `_now()`."""
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2022-12-31"], "granularity": "one_year", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.one_year": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "1 year", "title": "1 year", "interval": "1 year", "offset": "2 months"},
                }
            },
        )

        assert result == ["2020-03-01T00:00:00.000", "2021-03-01T00:00:00.000", "2022-03-01T00:00:00.000"]

    def test_two_months_with_origin_2019_01_01(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2021-12-31"], "granularity": "two_months", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.two_months": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "2 months", "title": "2 months", "interval": "2 months", "origin": "2019-01-01"},
                }
            },
        )

        assert result == [
            "2021-01-01T00:00:00.000",
            "2021-03-01T00:00:00.000",
            "2021-05-01T00:00:00.000",
            "2021-07-01T00:00:00.000",
            "2021-09-01T00:00:00.000",
            "2021-11-01T00:00:00.000",
        ]

    def test_two_months_no_origin_no_offset(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2021-12-31"], "granularity": "two_months", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.two_months": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "2 months", "title": "2 months", "interval": "2 months"},
                }
            },
        )

        assert result == [
            "2021-01-01T00:00:00.000",
            "2021-03-01T00:00:00.000",
            "2021-05-01T00:00:00.000",
            "2021-07-01T00:00:00.000",
            "2021-09-01T00:00:00.000",
            "2021-11-01T00:00:00.000",
        ]

    def test_two_months_with_origin_2019_03_15(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2021-12-31"], "granularity": "two_months", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.two_months": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "2 months", "title": "2 months", "interval": "2 months", "origin": "2019-03-15"},
                }
            },
        )

        assert result == [
            "2020-11-15T00:00:00.000",
            "2021-01-15T00:00:00.000",
            "2021-03-15T00:00:00.000",
            "2021-05-15T00:00:00.000",
            "2021-07-15T00:00:00.000",
            "2021-09-15T00:00:00.000",
            "2021-11-15T00:00:00.000",
        ]

    def test_one_month_two_weeks_three_days_with_origin(self):
        rs = ResultSet({})
        time_dimension = {
            "dateRange": ["2021-01-01", "2021-12-31"],
            "granularity": "one_mo_two_we_three_d",
            "dimension": "Events.time",
        }

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.one_mo_two_we_three_d": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {
                        "name": "1 months 2 weeks 3 days",
                        "title": "1 months 2 weeks 3 days",
                        "interval": "1 months 2 weeks 3 days",
                        "origin": "2021-01-25",
                    },
                }
            },
        )

        assert result == [
            "2020-12-08T00:00:00.000",
            "2021-01-25T00:00:00.000",
            "2021-03-14T00:00:00.000",
            "2021-05-01T00:00:00.000",
            "2021-06-18T00:00:00.000",
            "2021-08-04T00:00:00.000",
            "2021-09-21T00:00:00.000",
            "2021-11-07T00:00:00.000",
            "2021-12-24T00:00:00.000",
        ]

    def test_three_weeks_with_origin(self):
        rs = ResultSet({})
        time_dimension = {"dateRange": ["2021-01-01", "2021-03-01"], "granularity": "three_weeks", "dimension": "Events.time"}

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.three_weeks": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {"name": "3 weeks", "title": "3 weeks", "interval": "3 weeks", "origin": "2020-12-15"},
                }
            },
        )

        assert result == [
            "2020-12-15T00:00:00.000",
            "2021-01-05T00:00:00.000",
            "2021-01-26T00:00:00.000",
            "2021-02-16T00:00:00.000",
        ]

    def test_compound_interval_with_origin(self):
        rs = ResultSet({})
        time_dimension = {
            "dateRange": ["2021-01-01", "2021-12-31"],
            "granularity": "two_mo_3w_4d_5h_6m_7s",
            "dimension": "Events.time",
        }

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.two_mo_3w_4d_5h_6m_7s": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {
                        "name": "two_mo_3w_4d_5h_6m_7s",
                        "title": "two_mo_3w_4d_5h_6m_7s",
                        "interval": "2 months 3 weeks 4 days 5 hours 6 minutes 7 seconds",
                        "origin": "2021-01-01",
                    },
                }
            },
        )

        assert result == [
            "2021-01-01T00:00:00.000",
            "2021-03-26T05:06:07.000",
            "2021-06-20T10:12:14.000",
            "2021-09-14T15:18:21.000",
            "2021-12-09T20:24:28.000",
        ]

    def test_minutes_seconds_interval_with_origin(self):
        rs = ResultSet({})
        time_dimension = {
            "dateRange": ["2021-02-01 10:00:00", "2021-02-01 12:00:00"],
            "granularity": "ten_min_fifteen_sec",
            "dimension": "Events.time",
        }

        result = rs.time_series(
            time_dimension,
            1,
            {
                "Events.time.ten_min_fifteen_sec": {
                    "title": "Time Dimension",
                    "shortTitle": "TD",
                    "type": "time",
                    "granularity": {
                        "name": "10 minutes 15 seconds",
                        "title": "10 minutes 15 seconds",
                        "interval": "10 minutes 15 seconds",
                        "origin": "2021-02-01 09:59:45",
                    },
                }
            },
        )

        assert result == [
            "2021-02-01T09:59:45.000",
            "2021-02-01T10:10:00.000",
            "2021-02-01T10:20:15.000",
            "2021-02-01T10:30:30.000",
            "2021-02-01T10:40:45.000",
            "2021-02-01T10:51:00.000",
            "2021-02-01T11:01:15.000",
            "2021-02-01T11:11:30.000",
            "2021-02-01T11:21:45.000",
            "2021-02-01T11:32:00.000",
            "2021-02-01T11:42:15.000",
            "2021-02-01T11:52:30.000",
        ]
