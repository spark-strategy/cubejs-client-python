"""Fixtures transcribed verbatim from the JS SDK's
compare-date-range.test.ts and test/fixtures/datablending/load-responses.json,
for compareDateRangeQuery/blendingQuery golden tests.
"""

COMPARE_DATE_RANGE_LOAD_RESPONSES = [
    {
        "queryType": "compareDateRangeQuery",
        "results": [
            {
                "query": {
                    "measures": ["Orders.count"],
                    "timeDimensions": [
                        {
                            "dimension": "Orders.ts",
                            "granularity": "day",
                            "dateRange": ["2020-08-10T00:00:00.000", "2020-08-16T23:59:59.999"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                    "dimensions": [],
                },
                "data": [
                    {
                        "Orders.ts.day": "2020-08-10T00:00:00.000",
                        "Orders.ts": "2020-08-10T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999",
                    },
                    {
                        "Orders.ts.day": "2020-08-12T00:00:00.000",
                        "Orders.ts": "2020-08-12T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999",
                    },
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
            },
            {
                "query": {
                    "measures": ["Orders.count"],
                    "timeDimensions": [
                        {
                            "dimension": "Orders.ts",
                            "granularity": "day",
                            "dateRange": ["2020-08-03T00:00:00.000", "2020-08-09T23:59:59.999"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                    "dimensions": [],
                },
                "data": [
                    {
                        "Orders.ts.day": "2020-08-03T00:00:00.000",
                        "Orders.ts": "2020-08-03T00:00:00.000",
                        "Orders.count": 2,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Orders.ts.day": "2020-08-04T00:00:00.000",
                        "Orders.ts": "2020-08-04T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Orders.ts.day": "2020-08-06T00:00:00.000",
                        "Orders.ts": "2020-08-06T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Orders.ts.day": "2020-08-08T00:00:00.000",
                        "Orders.ts": "2020-08-08T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
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
            },
        ],
        "pivotQuery": {
            "measures": ["Orders.count"],
            "timeDimensions": [
                {
                    "dimension": "Orders.ts",
                    "granularity": "day",
                    "dateRange": ["2020-08-10T00:00:00.000", "2020-08-16T23:59:59.999"],
                }
            ],
            "filters": [],
            "timezone": "UTC",
            "order": [],
            "dimensions": ["compareDateRange"],
            "queryType": "compareDateRangeQuery",
        },
    },
    {
        "queryType": "compareDateRangeQuery",
        "results": [
            {
                "query": {
                    "measures": ["Orders.count"],
                    "dimensions": ["Users.country"],
                    "timeDimensions": [
                        {
                            "dimension": "Orders.ts",
                            "granularity": "day",
                            "dateRange": ["2020-08-10T00:00:00.000", "2020-08-16T23:59:59.999"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                },
                "data": [
                    {
                        "Users.country": "US",
                        "Orders.ts.day": "2020-08-10T00:00:00.000",
                        "Orders.ts": "2020-08-10T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999",
                    },
                    {
                        "Users.country": "France",
                        "Orders.ts.day": "2020-08-12T00:00:00.000",
                        "Orders.ts": "2020-08-12T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999",
                    },
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
                    "dimensions": {
                        "Users.country": {"title": "Users Country", "shortTitle": "Country", "type": "string"}
                    },
                    "segments": {},
                    "timeDimensions": {
                        "Orders.ts.day": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                        "Orders.ts": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                    },
                },
            },
            {
                "query": {
                    "measures": ["Orders.count"],
                    "dimensions": ["Users.country"],
                    "timeDimensions": [
                        {
                            "dimension": "Orders.ts",
                            "granularity": "day",
                            "dateRange": ["2020-08-03T00:00:00.000", "2020-08-09T23:59:59.999"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                    "order": [],
                },
                "data": [
                    {
                        "Users.country": "Australia",
                        "Orders.ts.day": "2020-08-03T00:00:00.000",
                        "Orders.ts": "2020-08-03T00:00:00.000",
                        "Orders.count": 2,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Users.country": "France",
                        "Orders.ts.day": "2020-08-04T00:00:00.000",
                        "Orders.ts": "2020-08-04T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Users.country": "US",
                        "Orders.ts.day": "2020-08-06T00:00:00.000",
                        "Orders.ts": "2020-08-06T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
                    {
                        "Users.country": "France",
                        "Orders.ts.day": "2020-08-08T00:00:00.000",
                        "Orders.ts": "2020-08-08T00:00:00.000",
                        "Orders.count": 1,
                        "compareDateRange": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999",
                    },
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
                    "dimensions": {
                        "Users.country": {"title": "Users Country", "shortTitle": "Country", "type": "string"}
                    },
                    "segments": {},
                    "timeDimensions": {
                        "Orders.ts.day": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                        "Orders.ts": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                    },
                },
            },
        ],
        "pivotQuery": {
            "measures": ["Orders.count"],
            "dimensions": ["compareDateRange", "Users.country"],
            "timeDimensions": [
                {
                    "dimension": "Orders.ts",
                    "granularity": "day",
                    "dateRange": ["2020-08-03T00:00:00.000", "2020-08-09T23:59:59.999"],
                }
            ],
            "filters": [],
            "timezone": "UTC",
            "order": [],
            "queryType": "compareDateRangeQuery",
        },
    },
]

# Ported from test/fixtures/datablending/load-responses.json
BLENDING_LOAD_RESPONSE = {
    "queryType": "blendingQuery",
    "results": [
        {
            "query": {
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
            },
            "data": [
                {
                    "Orders.ts.day": "2020-08-01T00:00:00.000",
                    "Orders.ts": "2020-08-01T00:00:00.000",
                    "Orders.count": 1,
                    "time.day": "2020-08-01T00:00:00.000",
                },
                {
                    "Orders.ts.day": "2020-08-02T00:00:00.000",
                    "Orders.ts": "2020-08-02T00:00:00.000",
                    "Orders.count": 2,
                    "time.day": "2020-08-02T00:00:00.000",
                },
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
        },
        {
            "query": {
                "measures": ["Users.count"],
                "timeDimensions": [
                    {
                        "dimension": "Users.ts",
                        "granularity": "day",
                        "dateRange": ["2020-08-01T00:00:00.000", "2020-08-07T23:59:59.999"],
                    }
                ],
                "filters": [],
                "timezone": "UTC",
                "order": [],
                "dimensions": ["Users.country"],
            },
            "data": [
                {
                    "Users.ts.day": "2020-08-01T00:00:00.000",
                    "Users.ts": "2020-08-01T00:00:00.000",
                    "Users.count": 20,
                    "Users.country": "Australia",
                    "time.day": "2020-08-01T00:00:00.000",
                },
                {
                    "Users.ts.day": "2020-08-05T00:00:00.000",
                    "Users.ts": "2020-08-05T00:00:00.000",
                    "Users.count": 34,
                    "Users.country": "Spain",
                    "time.day": "2020-08-05T00:00:00.000",
                },
                {
                    "Users.ts.day": "2020-08-05T00:00:00.000",
                    "Users.ts": "2020-08-05T00:00:00.000",
                    "Users.count": 18,
                    "Users.country": "Italy",
                    "time.day": "2020-08-05T00:00:00.000",
                },
            ],
            "annotation": {
                "measures": {
                    "Users.count": {
                        "title": "Users Count",
                        "shortTitle": "Count",
                        "type": "number",
                        "drillMembers": [],
                        "drillMembersGrouped": {"measures": [], "dimensions": []},
                    }
                },
                "dimensions": {
                    "Users.country": {"title": "Users Country", "shortTitle": "Country", "type": "string"}
                },
                "segments": {},
                "timeDimensions": {
                    "Users.ts.day": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                    "Users.ts": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                },
            },
        },
    ],
    "pivotQuery": {
        "measures": ["Orders.count", "Users.count"],
        "timeDimensions": [
            {
                "dimension": "time",
                "granularity": "day",
                "dateRange": ["2020-08-01T00:00:00.000", "2020-08-07T23:59:59.999"],
            }
        ],
        "dimensions": ["Users.country"],
    },
}

BLENDING_LOAD_RESPONSE_WITHOUT_DATE_RANGE = {
    "queryType": "blendingQuery",
    "results": [
        {
            "query": {
                "measures": ["Orders.count"],
                "timeDimensions": [{"dimension": "Orders.ts", "granularity": "day"}],
                "filters": [],
                "timezone": "UTC",
                "order": [],
                "dimensions": [],
            },
            "data": [
                {
                    "Orders.ts.day": "2020-08-01T00:00:00.000",
                    "Orders.ts": "2020-08-01T00:00:00.000",
                    "Orders.count": 1,
                    "time.day": "2020-08-01T00:00:00.000",
                },
                {
                    "Orders.ts.day": "2020-08-02T00:00:00.000",
                    "Orders.ts": "2020-08-02T00:00:00.000",
                    "Orders.count": 2,
                    "time.day": "2020-08-02T00:00:00.000",
                },
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
        },
        {
            "query": {
                "measures": ["Users.count"],
                "timeDimensions": [{"dimension": "Users.ts", "granularity": "day"}],
                "filters": [],
                "timezone": "UTC",
                "order": [],
                "dimensions": ["Users.country"],
            },
            "data": [
                {
                    "Users.ts.day": "2020-08-01T00:00:00.000",
                    "Users.ts": "2020-08-01T00:00:00.000",
                    "Users.count": 20,
                    "Users.country": "Australia",
                    "time.day": "2020-08-01T00:00:00.000",
                },
                {
                    "Users.ts.day": "2020-08-05T00:00:00.000",
                    "Users.ts": "2020-08-05T00:00:00.000",
                    "Users.count": 34,
                    "Users.country": "Spain",
                    "time.day": "2020-08-05T00:00:00.000",
                },
                {
                    "Users.ts.day": "2020-08-05T00:00:00.000",
                    "Users.ts": "2020-08-05T00:00:00.000",
                    "Users.count": 18,
                    "Users.country": "Italy",
                    "time.day": "2020-08-05T00:00:00.000",
                },
            ],
            "annotation": {
                "measures": {
                    "Users.count": {
                        "title": "Users Count",
                        "shortTitle": "Count",
                        "type": "number",
                        "drillMembers": [],
                        "drillMembersGrouped": {"measures": [], "dimensions": []},
                    }
                },
                "dimensions": {
                    "Users.country": {"title": "Users Country", "shortTitle": "Country", "type": "string"}
                },
                "segments": {},
                "timeDimensions": {
                    "Users.ts.day": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                    "Users.ts": {"title": "Orders Ts", "shortTitle": "Ts", "type": "time"},
                },
            },
        },
    ],
    "pivotQuery": {
        "measures": ["Orders.count", "Users.count"],
        "timeDimensions": [{"dimension": "time", "granularity": "day"}],
        "dimensions": ["Users.country"],
    },
}


def _single_measure_blending_load_response():
    """Ported from data-blending.test.ts 'query with a single measure' /
    'query with a single measure and a custom series alias' (identical fixture,
    shared by both tests)."""
    return {
        "queryType": "blendingQuery",
        "results": [
            {
                "query": {
                    "measures": ["Users.count"],
                    "timeDimensions": [
                        {
                            "dimension": "Users.ts",
                            "granularity": "month",
                            "dateRange": ["2020-07-01T00:00:00.000", "2020-11-01T00:00:00.000"],
                        }
                    ],
                    "filters": [],
                    "order": [],
                    "dimensions": [],
                },
                "data": [
                    {
                        "Users.ts.month": "2020-08-01T00:00:00.000",
                        "Users.ts": "2020-08-01T00:00:00.000",
                        "Users.count": 14,
                        "time.month": "2020-08-01T00:00:00.000",
                    },
                    {
                        "Users.ts.month": "2020-09-01T00:00:00.000",
                        "Users.ts": "2020-09-01T00:00:00.000",
                        "Users.count": 23,
                        "time.month": "2020-09-01T00:00:00.000",
                    },
                ],
                "annotation": {
                    "measures": {
                        "Users.count": {
                            "title": "Users Count",
                            "shortTitle": "Count",
                            "type": "number",
                            "drillMembers": ["Users.id", "Users.name"],
                            "drillMembersGrouped": {"measures": [], "dimensions": ["Users.id", "Users.name"]},
                        }
                    },
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "Users.ts.month": {"title": "Users Ts", "shortTitle": "Ts", "type": "time"},
                        "Users.ts": {"title": "Users Ts", "shortTitle": "Ts", "type": "time"},
                    },
                },
            },
            {
                "query": {
                    "measures": ["Users.count"],
                    "timeDimensions": [
                        {
                            "dimension": "Users.ts",
                            "granularity": "month",
                            "dateRange": ["2020-07-01T00:00:00.000", "2020-11-01T00:00:00.000"],
                        }
                    ],
                    "filters": [{"member": "Users.country", "operator": "equals", "value": ["USA"]}],
                    "order": [],
                },
                "data": [
                    {
                        "Users.ts.month": "2020-08-01T00:00:00.000",
                        "Users.ts": "2020-08-01T00:00:00.000",
                        "Users.count": 2,
                        "time.month": "2020-08-01T00:00:00.000",
                    },
                    {
                        "Users.ts.month": "2020-09-01T00:00:00.000",
                        "Users.ts": "2020-09-05T00:00:00.000",
                        "Users.count": 4,
                        "time.month": "2020-09-01T00:00:00.000",
                    },
                    {
                        "Users.ts.month": "2020-10-01T00:00:00.000",
                        "Users.ts": "2020-10-05T00:00:00.000",
                        "Users.count": 7,
                        "time.month": "2020-10-01T00:00:00.000",
                    },
                ],
                "annotation": {
                    "measures": {
                        "Users.count": {
                            "title": "Users Count",
                            "shortTitle": "Count",
                            "type": "number",
                            "drillMembers": [],
                            "drillMembersGrouped": {"measures": [], "dimensions": []},
                        }
                    },
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "Users.ts.month": {"title": "Users Ts", "shortTitle": "Ts", "type": "time"},
                        "Users.ts": {"title": "Users Ts", "shortTitle": "Ts", "type": "time"},
                    },
                },
            },
        ],
        "pivotQuery": {
            "measures": ["Users.count", "Users.count"],
            "timeDimensions": [
                {
                    "dimension": "time",
                    "granularity": "month",
                    "dateRange": ["2020-07-01T00:00:00.000", "2020-11-01T00:00:00.000"],
                }
            ],
            "dimensions": [],
        },
    }


SINGLE_MEASURE_BLENDING_LOAD_RESPONSE = _single_measure_blending_load_response()
