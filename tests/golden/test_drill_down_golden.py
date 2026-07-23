"""Golden tests for ResultSet.drill_down(), ported verbatim from
drill-down.test.ts in the JS SDK."""

import datetime as dt

from cubejs_client.core import time_series
from cubejs_client.core.result_set import ResultSet


def _load_response(query_overrides=None):
    query_overrides = query_overrides or {}
    query = {
        "measures": ["Orders.count"],
        "timeDimensions": [
            {
                "dimension": "Orders.ts",
                "granularity": "day",
                "dateRange": ["2020-08-01T00:00:00.000", "2020-08-07T23:59:59.999"],
            }
        ],
        "filters": [],
        "timezone": "UTC",
        "order": [],
        "dimensions": [],
        **query_overrides,
    }
    return {
        "queryType": "regularQuery",
        "results": [
            {
                "query": query,
                "data": [
                    {"Orders.ts.day": "2020-08-01T00:00:00.000", "Orders.ts": "2020-08-01T00:00:00.000", "Orders.count": 1},
                    {"Orders.ts.day": "2020-08-02T00:00:00.000", "Orders.ts": "2020-08-02T00:00:00.000", "Orders.count": 2},
                ],
                "annotation": {
                    "measures": {
                        "Orders.count": {
                            "title": "Orders Count",
                            "shortTitle": "Count",
                            "type": "number",
                            "drillMembers": ["Orders.id", "Orders.title"],
                            "drillMembersGrouped": {"measures": [], "dimensions": ["Orders.id", "Orders.title"]},
                        }
                    },
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "Orders.ts.day": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                        "Orders.ts": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                    },
                },
            }
        ],
        "pivotQuery": {
            "measures": ["Orders.count"],
            "timeDimensions": [
                {
                    "dimension": "Orders.ts",
                    "granularity": "day",
                    "dateRange": ["2020-08-01T00:00:00.000", "2020-08-07T23:59:59.999"],
                }
            ],
            "filters": [],
            "timezone": "UTC",
            "order": [],
            "dimensions": [],
            **query_overrides,
        },
    }


_LOAD_RESPONSE_2 = {
    "queryType": "regularQuery",
    "results": [
        {
            "query": {
                "measures": ["Orders.count"],
                "timeDimensions": [
                    {
                        "dimension": "Orders.createdAt",
                        "granularity": "week",
                        "dateRange": ["2023-05-10T00:00:00.000", "2023-05-14T23:59:59.999"],
                    }
                ],
                "limit": 10000,
                "timezone": "UTC",
                "order": [],
                "filters": [],
                "dimensions": [],
                "rowLimit": 10000,
                "queryType": "regularQuery",
            },
            "data": [
                {
                    "Orders.createdAt.week": "2023-05-08T00:00:00.000",
                    "Orders.createdAt": "2023-05-08T00:00:00.000",
                    "Orders.count": "21",
                }
            ],
            "annotation": {
                "measures": {
                    "Orders.count": {
                        "title": "Orders Count",
                        "shortTitle": "Count",
                        "type": "number",
                        "drillMembers": ["Orders.id", "Orders.createdAt"],
                        "drillMembersGrouped": {"measures": [], "dimensions": ["Orders.id", "Orders.createdAt"]},
                    }
                },
                "dimensions": {},
                "segments": {},
                "timeDimensions": {
                    "Orders.createdAt.week": {"title": "Orders Created at", "shortTitle": "Created at", "type": "time"},
                    "Orders.createdAt": {"title": "Orders Created at", "shortTitle": "Created at", "type": "time"},
                },
            },
        }
    ],
    "pivotQuery": {
        "measures": ["Orders.count"],
        "timeDimensions": [
            {
                "dimension": "Orders.createdAt",
                "granularity": "week",
                "dateRange": ["2023-05-10T00:00:00.000", "2023-05-14T23:59:59.999"],
            }
        ],
        "limit": 10000,
        "timezone": "UTC",
        "order": [],
        "filters": [],
        "dimensions": [],
        "rowLimit": 10000,
        "queryType": "regularQuery",
    },
}


def test_handles_a_query_with_a_time_dimension():
    rs = ResultSet(_load_response())

    assert rs.drill_down({"xValues": ["2020-08-01T00:00:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [{"member": "Orders.count", "operator": "measureFilter"}],
        "timeDimensions": [{"dimension": "Orders.ts", "dateRange": ["2020-08-01T00:00:00.000", "2020-08-01T23:59:59.999"]}],
        "timezone": "UTC",
    }


def test_respects_the_time_zone():
    rs = ResultSet(_load_response({"timezone": "America/Los_Angeles"}))

    assert rs.drill_down({"xValues": ["2020-08-01T00:00:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [{"member": "Orders.count", "operator": "measureFilter"}],
        "timeDimensions": [{"dimension": "Orders.ts", "dateRange": ["2020-08-01T00:00:00.000", "2020-08-01T23:59:59.999"]}],
        "timezone": "America/Los_Angeles",
    }


def test_propagates_parent_filters():
    rs = ResultSet(
        _load_response({"filters": [{"member": "Users.country", "operator": "equals", "values": ["Los Angeles"]}]})
    )

    assert rs.drill_down({"xValues": ["2020-08-01T00:00:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [
            {"member": "Orders.count", "operator": "measureFilter"},
            {"member": "Users.country", "operator": "equals", "values": ["Los Angeles"]},
        ],
        "timeDimensions": [{"dimension": "Orders.ts", "dateRange": ["2020-08-01T00:00:00.000", "2020-08-01T23:59:59.999"]}],
        "timezone": "UTC",
    }


def test_handles_null_values():
    rs = ResultSet(_load_response({"dimensions": ["Statuses.potential"], "timeDimensions": []}))

    assert rs.drill_down({"xValues": []}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [
            {"member": "Orders.count", "operator": "measureFilter"},
            {"member": "Statuses.potential", "operator": "notSet"},
        ],
        "timeDimensions": [],
        "timezone": "UTC",
    }


def test_respects_the_parent_time_dimension_date_range():
    rs = ResultSet(_LOAD_RESPONSE_2)

    assert rs.drill_down({"xValues": ["2023-05-08T00:00:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.createdAt"],
        "filters": [{"member": "Orders.count", "operator": "measureFilter"}],
        "timeDimensions": [
            {"dimension": "Orders.createdAt", "dateRange": ["2023-05-10T00:00:00.000", "2023-05-14T23:59:59.999"]}
        ],
        "timezone": "UTC",
    }


def test_snaps_date_range_to_granularity_when_not_defined_in_time_dimension():
    rs = ResultSet(_load_response({"timeDimensions": [{"dimension": "Orders.ts", "granularity": "week"}]}))

    assert rs.drill_down({"xValues": ["2020-08-01T00:00:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [{"member": "Orders.count", "operator": "measureFilter"}],
        "timeDimensions": [{"dimension": "Orders.ts", "dateRange": ["2020-07-27T00:00:00.000", "2020-08-02T23:59:59.999"]}],
        "timezone": "UTC",
    }


def _custom_granularity_response(origin: str):
    return {
        "queryType": "regularQuery",
        "results": [
            {
                "query": {
                    "measures": ["Transactions.count"],
                    "timeDimensions": [
                        {
                            "dimension": "Transactions.createdAt",
                            "granularity": "alerting_monitor",
                            "dateRange": ["2020-08-01T00:00:00.000", "2020-08-01T01:00:00.000"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                    "dimensions": [],
                },
                "data": [
                    {
                        "Transactions.createdAt.alerting_monitor": "2020-08-01T00:00:00.000",
                        "Transactions.createdAt": "2020-08-01T00:00:00.000",
                        "Transactions.count": 10,
                    },
                    {
                        "Transactions.createdAt.alerting_monitor": "2020-08-01T00:05:00.000",
                        "Transactions.createdAt": "2020-08-01T00:05:00.000",
                        "Transactions.count": 15,
                    },
                    {
                        "Transactions.createdAt.alerting_monitor": "2020-08-01T00:10:00.000",
                        "Transactions.createdAt": "2020-08-01T00:10:00.000",
                        "Transactions.count": 8,
                    },
                ],
                "annotation": {
                    "measures": {
                        "Transactions.count": {
                            "title": "Transactions Count",
                            "shortTitle": "Count",
                            "type": "number",
                            "drillMembers": ["Transactions.id", "Transactions.createdAt"],
                            "drillMembersGrouped": {
                                "measures": [],
                                "dimensions": ["Transactions.id", "Transactions.createdAt"],
                            },
                        }
                    },
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "Transactions.createdAt.alerting_monitor": {
                            "title": "Transaction created at",
                            "shortTitle": "Created at",
                            "type": "time",
                            "granularity": {
                                "name": "alerting_monitor",
                                "title": "Alerting Monitor",
                                "interval": "5 minutes",
                                "origin": origin,
                            },
                        },
                        "Transactions.createdAt": {
                            "title": "Transaction created at",
                            "shortTitle": "Created at",
                            "type": "time",
                        },
                    },
                },
            }
        ],
        "pivotQuery": {
            "measures": ["Transactions.count"],
            "timeDimensions": [
                {
                    "dimension": "Transactions.createdAt",
                    "granularity": "alerting_monitor",
                    "dateRange": ["2020-08-01T00:00:00.000", "2020-08-01T01:00:00.000"],
                }
            ],
            "filters": [],
            "timezone": "UTC",
            "order": [],
            "dimensions": [],
        },
    }


def test_handles_custom_granularity_with_interval_and_origin():
    rs = ResultSet(_custom_granularity_response(origin="2020-08-01T00:00:00.000"))

    assert rs.drill_down({"xValues": ["2020-08-01T00:05:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Transactions.id", "Transactions.createdAt"],
        "filters": [{"member": "Transactions.count", "operator": "measureFilter"}],
        "timeDimensions": [
            {"dimension": "Transactions.createdAt", "dateRange": ["2020-08-01T00:05:00.000", "2020-08-01T00:09:59.999"]}
        ],
        "timezone": "UTC",
    }


def test_handles_custom_granularity_with_non_aligned_origin():
    rs = ResultSet(_custom_granularity_response(origin="2020-08-01T00:02:00.000"))

    assert rs.drill_down({"xValues": ["2020-08-01T00:07:00.000"]}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Transactions.id", "Transactions.createdAt"],
        "filters": [{"member": "Transactions.count", "operator": "measureFilter"}],
        "timeDimensions": [
            {"dimension": "Transactions.createdAt", "dateRange": ["2020-08-01T00:07:00.000", "2020-08-01T00:11:59.999"]}
        ],
        "timezone": "UTC",
    }


def test_missing_x_value_for_a_time_granularity_member_drills_into_now(monkeypatch):
    """Not JS-test-derived: no case in drill-down.test.ts exercises a
    time-granularity member with no corresponding drilled value. JS's
    `dayjs(undefined)` silently resolves to "now" rather than erroring, and
    `drillDown` relies on that — mirrored here via `parse_datetime(None)`
    (see time_series.py). `_now()` is monkeypatched for a deterministic
    assertion."""
    monkeypatch.setattr(time_series, "_now", lambda: dt.datetime(2020, 8, 3, 15, 0, 0))

    rs = ResultSet(_load_response())

    assert rs.drill_down({"xValues": []}) == {
        "measures": [],
        "segments": [],
        "dimensions": ["Orders.id", "Orders.title"],
        "filters": [{"member": "Orders.count", "operator": "measureFilter"}],
        "timeDimensions": [{"dimension": "Orders.ts", "dateRange": ["2020-08-03T00:00:00.000", "2020-08-03T23:59:59.999"]}],
        "timezone": "UTC",
    }
