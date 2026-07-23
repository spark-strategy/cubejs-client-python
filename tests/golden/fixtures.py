"""Golden fixtures transcribed verbatim from the JS SDK's test/helpers.ts.

Source: packages/cubejs-client-core/test/helpers.ts in the cube-js/cube repo
(as of the commit this port was made against). Kept as a line-for-line
translation of the JS object literal into a Python dict so it can serve as
cross-language ground truth for ResultSet golden tests.
"""

DESCRIPTIVE_QUERY_REQUEST = {
    "timeDimensions": [
        {"dimension": "base_orders.created_at", "granularity": "month"},
        {
            "dimension": "base_orders.completed_at",
            "dateRange": ["2023-05-16", "2025-05-16"],
        },
    ],
    "filters": [{"member": "base_orders.fiscal_event_date_label", "operator": "set"}],
    "dimensions": ["base_orders.status"],
    "measures": ["base_orders.count"],
    "segments": ["users.sf_users"],
}

DESCRIPTIVE_QUERY_RESPONSE = {
    "queryType": "regularQuery",
    "results": [
        {
            "query": {
                "measures": ["base_orders.count"],
                "dimensions": ["base_orders.status"],
                "timeDimensions": [
                    {"dimension": "base_orders.created_at", "granularity": "month"},
                    {
                        "dimension": "base_orders.completed_at",
                        "dateRange": [
                            "2023-05-16T00:00:00.000",
                            "2025-05-16T23:59:59.999",
                        ],
                    },
                ],
                "segments": ["users.sf_users"],
                "limit": 10000,
                "total": True,
                "timezone": "UTC",
                "filters": [{"member": "base_orders.fiscal_event_date_label", "operator": "set"}],
                "rowLimit": 10000,
            },
            "lastRefreshTime": "2025-05-16T13:34:38.144Z",
            "usedPreAggregations": {},
            "requestId": "2ac2a7b1-008b-41ec-be93-691f79a55348-span-1",
            "annotation": {
                "measures": {
                    "base_orders.count": {
                        "title": "Base Orders Count",
                        "shortTitle": "Count",
                        "type": "number",
                        "drillMembers": [
                            "base_orders.id",
                            "base_orders.status",
                            "users.city",
                            "users.gender",
                        ],
                        "drillMembersGrouped": {
                            "measures": [],
                            "dimensions": [
                                "base_orders.id",
                                "base_orders.status",
                                "users.city",
                                "users.gender",
                            ],
                        },
                    }
                },
                "dimensions": {
                    "base_orders.status": {
                        "title": "Base Orders Status",
                        "shortTitle": "Status",
                        "type": "string",
                        "meta": {"addDesc": "The status of order", "moreNum": 42},
                    }
                },
                "timeDimensions": {
                    "base_orders.created_at": {
                        "title": "Base Orders Created at",
                        "shortTitle": "Created at",
                        "type": "time",
                    },
                    "base_orders.created_at.month": {
                        "title": "Base Orders Created at",
                        "shortTitle": "Created at",
                        "type": "time",
                        "granularity": {"name": "month", "title": "month", "interval": "1 month"},
                    },
                },
                "segments": {
                    "users.sf_users": {"title": "Users Sf Users", "shortTitle": "Sf Users"}
                },
            },
            "dataSource": "default",
            "dbType": "postgres",
            "extDbType": "cubestore",
            "external": False,
            "slowQuery": False,
            "total": 19,
            "data": [
                {
                    "base_orders.created_at.month": "2023-04-01T00:00:00.000",
                    "base_orders.created_at": "2023-04-01T00:00:00.000",
                    "base_orders.count": "2",
                    "base_orders.status": "completed",
                },
                {
                    "base_orders.count": "6",
                    "base_orders.created_at": "2023-05-01T00:00:00.000",
                    "base_orders.created_at.month": "2023-05-01T00:00:00.000",
                    "base_orders.status": "completed",
                },
                {
                    "base_orders.count": "6",
                    "base_orders.status": "processing",
                    "base_orders.created_at": "2023-05-01T00:00:00.000",
                    "base_orders.created_at.month": "2023-05-01T00:00:00.000",
                },
                {
                    "base_orders.count": "9",
                    "base_orders.created_at.month": "2023-05-01T00:00:00.000",
                    "base_orders.status": "shipped",
                    "base_orders.created_at": "2023-05-01T00:00:00.000",
                },
                {
                    "base_orders.created_at": "2023-06-01T00:00:00.000",
                    "base_orders.status": "completed",
                    "base_orders.created_at.month": "2023-06-01T00:00:00.000",
                    "base_orders.count": "5",
                },
                {
                    "base_orders.count": "5",
                    "base_orders.status": "processing",
                    "base_orders.created_at": "2023-06-01T00:00:00.000",
                    "base_orders.created_at.month": "2023-06-01T00:00:00.000",
                },
                {
                    "base_orders.count": "13",
                    "base_orders.created_at": "2023-06-01T00:00:00.000",
                    "base_orders.status": "shipped",
                    "base_orders.created_at.month": "2023-06-01T00:00:00.000",
                },
                {
                    "base_orders.status": "completed",
                    "base_orders.created_at.month": "2023-07-01T00:00:00.000",
                    "base_orders.created_at": "2023-07-01T00:00:00.000",
                    "base_orders.count": "5",
                },
                {
                    "base_orders.created_at.month": "2023-07-01T00:00:00.000",
                    "base_orders.status": "processing",
                    "base_orders.created_at": "2023-07-01T00:00:00.000",
                    "base_orders.count": "7",
                },
                {
                    "base_orders.count": "5",
                    "base_orders.status": "shipped",
                    "base_orders.created_at": "2023-07-01T00:00:00.000",
                    "base_orders.created_at.month": "2023-07-01T00:00:00.000",
                },
                {
                    "base_orders.created_at": "2023-08-01T00:00:00.000",
                    "base_orders.status": "completed",
                    "base_orders.count": "11",
                    "base_orders.created_at.month": "2023-08-01T00:00:00.000",
                },
                {
                    "base_orders.count": "3",
                    "base_orders.created_at.month": "2023-08-01T00:00:00.000",
                    "base_orders.created_at": "2023-08-01T00:00:00.000",
                    "base_orders.status": "processing",
                },
                {
                    "base_orders.status": "shipped",
                    "base_orders.count": "4",
                    "base_orders.created_at.month": "2023-08-01T00:00:00.000",
                    "base_orders.created_at": "2023-08-01T00:00:00.000",
                },
                {
                    "base_orders.created_at.month": "2023-09-01T00:00:00.000",
                    "base_orders.status": "completed",
                    "base_orders.count": "5",
                    "base_orders.created_at": "2023-09-01T00:00:00.000",
                },
                {
                    "base_orders.count": "10",
                    "base_orders.created_at.month": "2023-09-01T00:00:00.000",
                    "base_orders.status": "processing",
                    "base_orders.created_at": "2023-09-01T00:00:00.000",
                },
                {
                    "base_orders.created_at": "2023-09-01T00:00:00.000",
                    "base_orders.count": "9",
                    "base_orders.created_at.month": "2023-09-01T00:00:00.000",
                    "base_orders.status": "shipped",
                },
                {
                    "base_orders.count": "4",
                    "base_orders.created_at.month": "2023-10-01T00:00:00.000",
                    "base_orders.created_at": "2023-10-01T00:00:00.000",
                    "base_orders.status": "completed",
                },
                {
                    "base_orders.count": "5",
                    "base_orders.created_at": "2023-10-01T00:00:00.000",
                    "base_orders.status": "processing",
                    "base_orders.created_at.month": "2023-10-01T00:00:00.000",
                },
                {
                    "base_orders.status": "shipped",
                    "base_orders.created_at.month": "2023-10-01T00:00:00.000",
                    "base_orders.count": "9",
                    "base_orders.created_at": "2023-10-01T00:00:00.000",
                },
            ],
        }
    ],
    "pivotQuery": {
        "measures": ["base_orders.count"],
        "dimensions": ["base_orders.status"],
        "timeDimensions": [
            {"dimension": "base_orders.created_at", "granularity": "month"},
            {
                "dimension": "base_orders.completed_at",
                "dateRange": ["2023-05-16T00:00:00.000", "2025-05-16T23:59:59.999"],
            },
        ],
        "segments": ["users.sf_users"],
        "limit": 10000,
        "total": True,
        "timezone": "UTC",
        "filters": [{"member": "base_orders.fiscal_event_date_label", "operator": "set"}],
        "rowLimit": 10000,
        "queryType": "regularQuery",
    },
    "slowQuery": False,
}

NUMERIC_CASTED_DATA = [
    {**row, "base_orders.count": float(row["base_orders.count"])}
    for row in DESCRIPTIVE_QUERY_RESPONSE["results"][0]["data"]
]
