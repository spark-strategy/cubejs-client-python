"""Golden tests ported from granularity.test.ts's chartPivot describe block.

The JS file also has a 'week granularity in other locale' test that re-runs
the same fixture after switching dayjs's global locale to Korean — that's a
JS-runtime-locale-isolation concern (this port has no locale concept: week
boundaries are hardcoded Monday-start, matching the JS SDK's internal
cube-specific locale regardless of the caller's dayjs locale), so only the
one locale-independent case is ported.
"""

from cubejs_client.core.result_set import ResultSet


def test_week_granularity():
    result = ResultSet(
        {
            "queryType": "regularQuery",
            "results": [
                {
                    "query": {
                        "measures": ["LineItems.count"],
                        "timeDimensions": [
                            {
                                "dimension": "LineItems.createdAt",
                                "granularity": "week",
                                "dateRange": ["2019-01-08T00:00:00.000", "2019-01-18T00:00:00.000"],
                            }
                        ],
                        "filters": [{"operator": "equals", "values": ["us-ut"], "member": "Users.state"}],
                        "limit": 2,
                        "rowLimit": 2,
                        "timezone": "UTC",
                        "order": [],
                        "dimensions": [],
                    },
                    "data": [
                        {
                            "LineItems.createdAt.week": "2019-01-07T00:00:00.000",
                            "LineItems.createdAt": "2019-01-07T00:00:00.000",
                            "LineItems.count": "2",
                        }
                    ],
                    "annotation": {
                        "measures": {
                            "LineItems.count": {
                                "title": "Line Items Count",
                                "shortTitle": "Count",
                                "type": "number",
                                "drillMembers": ["LineItems.id", "LineItems.createdAt"],
                                "drillMembersGrouped": {"measures": [], "dimensions": ["LineItems.id", "LineItems.createdAt"]},
                            }
                        },
                        "dimensions": {},
                        "segments": {},
                        "timeDimensions": {
                            "LineItems.createdAt.week": {"title": "Line Items Created at", "shortTitle": "Created at", "type": "time"},
                            "LineItems.createdAt": {"title": "Line Items Created at", "shortTitle": "Created at", "type": "time"},
                        },
                    },
                }
            ],
            "pivotQuery": {
                "measures": ["LineItems.count"],
                "timeDimensions": [
                    {
                        "dimension": "LineItems.createdAt",
                        "granularity": "week",
                        "dateRange": ["2019-01-08T00:00:00.000", "2019-01-18T00:00:00.000"],
                    }
                ],
                "filters": [{"operator": "equals", "values": ["us-ut"], "member": "Users.state"}],
                "limit": 2,
                "rowLimit": 2,
                "timezone": "UTC",
                "order": [],
                "dimensions": [],
                "queryType": "regularQuery",
            },
        }
    )

    assert result.chart_pivot() == [
        {"x": "2019-01-07T00:00:00.000", "xValues": ["2019-01-07T00:00:00.000"], "LineItems.count": 2},
        {"x": "2019-01-14T00:00:00.000", "xValues": ["2019-01-14T00:00:00.000"], "LineItems.count": 0},
    ]


def _hour_granularity_fixture(date_range):
    return {
        "queryType": "regularQuery",
        "results": [
            {
                "query": {
                    "measures": ["LineItems.count"],
                    "timeDimensions": [
                        {"dimension": "LineItems.createdAt", "granularity": "hour", "dateRange": date_range}
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                    "dimensions": [],
                },
                "data": [
                    {
                        "LineItems.createdAt.hour": f"2019-01-08T0{h}:00:00.000",
                        "LineItems.createdAt": f"2019-01-08T0{h}:00:00.000",
                        "LineItems.count": str(count),
                    }
                    for h, count in zip(range(1, 7), [2, 3, 4, 5, 6, 7])
                ],
                "annotation": {
                    "measures": {
                        "LineItems.count": {
                            "title": "Line Items Count",
                            "shortTitle": "Count",
                            "type": "number",
                            "drillMembers": ["LineItems.id", "LineItems.createdAt"],
                            "drillMembersGrouped": {"measures": [], "dimensions": ["LineItems.id", "LineItems.createdAt"]},
                        }
                    },
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "LineItems.createdAt.week": {"title": "Line Items Created at", "shortTitle": "Created at", "type": "time"},
                        "LineItems.createdAt": {"title": "Line Items Created at", "shortTitle": "Created at", "type": "time"},
                    },
                },
            }
        ],
        "pivotQuery": {
            "measures": ["LineItems.count"],
            "timeDimensions": [
                {"dimension": "LineItems.createdAt", "granularity": "hour", "dateRange": date_range}
            ],
            "filters": [],
            "timezone": "UTC",
            "order": [],
            "dimensions": [],
            "queryType": "regularQuery",
        },
    }


def test_hour_granularity_end_minutes_greater_than_start_minutes():
    result = ResultSet(_hour_granularity_fixture(["2019-01-08T01:45:25.342", "2019-01-08T07:45:58.399"]))

    assert result.chart_pivot() == [
        {"x": "2019-01-08T01:00:00.000", "xValues": ["2019-01-08T01:00:00.000"], "LineItems.count": 2},
        {"x": "2019-01-08T02:00:00.000", "xValues": ["2019-01-08T02:00:00.000"], "LineItems.count": 3},
        {"x": "2019-01-08T03:00:00.000", "xValues": ["2019-01-08T03:00:00.000"], "LineItems.count": 4},
        {"x": "2019-01-08T04:00:00.000", "xValues": ["2019-01-08T04:00:00.000"], "LineItems.count": 5},
        {"x": "2019-01-08T05:00:00.000", "xValues": ["2019-01-08T05:00:00.000"], "LineItems.count": 6},
        {"x": "2019-01-08T06:00:00.000", "xValues": ["2019-01-08T06:00:00.000"], "LineItems.count": 7},
        {"x": "2019-01-08T07:00:00.000", "xValues": ["2019-01-08T07:00:00.000"], "LineItems.count": 0},
    ]


def test_hour_granularity_end_minutes_less_than_start_minutes():
    result = ResultSet(_hour_granularity_fixture(["2019-01-08T01:45:25.342", "2019-01-08T07:35:58.399"]))

    assert result.chart_pivot() == [
        {"x": "2019-01-08T01:00:00.000", "xValues": ["2019-01-08T01:00:00.000"], "LineItems.count": 2},
        {"x": "2019-01-08T02:00:00.000", "xValues": ["2019-01-08T02:00:00.000"], "LineItems.count": 3},
        {"x": "2019-01-08T03:00:00.000", "xValues": ["2019-01-08T03:00:00.000"], "LineItems.count": 4},
        {"x": "2019-01-08T04:00:00.000", "xValues": ["2019-01-08T04:00:00.000"], "LineItems.count": 5},
        {"x": "2019-01-08T05:00:00.000", "xValues": ["2019-01-08T05:00:00.000"], "LineItems.count": 6},
        {"x": "2019-01-08T06:00:00.000", "xValues": ["2019-01-08T06:00:00.000"], "LineItems.count": 7},
        {"x": "2019-01-08T07:00:00.000", "xValues": ["2019-01-08T07:00:00.000"], "LineItems.count": 0},
    ]
