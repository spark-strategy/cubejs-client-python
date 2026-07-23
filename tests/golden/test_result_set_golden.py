"""Golden tests for ResultSet, ported from ResultSet.test.ts in the JS SDK.

Each test's input/expected-output pair is transcribed verbatim from the
JS test suite (packages/cubejs-client-core/test/ResultSet.test.ts) so that
the Python core's behavior can be verified against the JS ground truth.
"""

import datetime as dt

from cubejs_client.core.result_set import ResultSet

from .fixtures import DESCRIPTIVE_QUERY_RESPONSE


class TestChartPivotCoercion:
    """Ported from ResultSet.test.ts describe('chartPivot') (lines ~403-650)."""

    def _make(self, measure_key, measure_value, options=None):
        return ResultSet(
            {
                "query": {
                    "measures": [measure_key],
                    "dimensions": ["Foo.name"],
                    "filters": [],
                    "timezone": "UTC",
                    "timeDimensions": [],
                },
                "data": [{"Foo.name": "Name 1", measure_key: measure_value}],
                "lastRefreshTime": "2020-03-18T13:41:04.436Z",
                "usedPreAggregations": {},
                "annotation": {
                    "measures": {
                        measure_key: {"title": "Foo Count", "shortTitle": "Count", "type": "number"}
                    },
                    "dimensions": {
                        "Foo.name": {"title": "Foo Name", "shortTitle": "Name", "type": "string"}
                    },
                    "segments": {},
                    "timeDimensions": {},
                },
            },
            options or {},
        )

    def test_string_field(self):
        rs = self._make("Foo.count", "Some string")
        assert rs.chart_pivot() == [
            {"x": "Name 1", "Foo.count": "Some string", "xValues": ["Name 1"]}
        ]

    def test_null_field(self):
        rs = self._make("Foo.count", None)
        assert rs.chart_pivot() == [{"x": "Name 1", "Foo.count": 0, "xValues": ["Name 1"]}]

    def test_number_field(self):
        rs = self._make("Foo.count", "10")
        assert rs.chart_pivot() == [{"x": "Name 1", "Foo.count": 10, "xValues": ["Name 1"]}]

    def test_time_field_results(self):
        rs = self._make(
            "Foo.latestRun", "2020-03-11T18:06:09.403Z", options={"parseDateMeasures": True}
        )
        assert rs.chart_pivot() == [
            {
                "x": "Name 1",
                "Foo.latestRun": dt.datetime(2020, 3, 11, 18, 6, 9, 403000),
                "xValues": ["Name 1"],
            }
        ]


class TestPivotOrdering:
    def test_order_is_preserved(self):
        """Ported from ResultSet.test.ts 'order is preserved' (~line 1835)."""
        rs = ResultSet(
            {
                "query": {
                    "measures": ["User.total"],
                    "dimensions": ["User.visits"],
                    "filters": [],
                    "timezone": "UTC",
                },
                "data": [
                    {"User.total": 1, "User.visits": 1},
                    {"User.total": 15, "User.visits": 0.9},
                    {"User.total": 20, "User.visits": 0.7},
                    {"User.total": 10, "User.visits": 0},
                ],
                "annotation": {
                    "measures": {"User.total": {}},
                    "dimensions": {
                        "User.visits": {"title": "User Visits", "shortTitle": "Visits", "type": "number"}
                    },
                    "segments": {},
                    "timeDimensions": {},
                },
            }
        )

        assert rs.pivot() == [
            {"xValues": [1], "yValuesArray": [[["User.total"], 1]]},
            {"xValues": [0.9], "yValuesArray": [[["User.total"], 15]]},
            {"xValues": [0.7], "yValuesArray": [[["User.total"], 20]]},
            {"xValues": [0], "yValuesArray": [[["User.total"], 10]]},
        ]

    def test_table_pivot_keeps_null_values_on_non_matching_rows(self):
        """Ported from ResultSet.test.ts 'keeps null values on non-matching rows' (~line 1887)."""
        rs = ResultSet(
            {
                "query": {"dimensions": ["User.name", "Friend.name"]},
                "data": [{"User.name": "Bob", "Friend.name": None}],
            }
        )

        assert rs.table_pivot() == [{"User.name": "Bob", "Friend.name": None}]


class TestDescriptiveQueryResponse:
    """Ported from ResultSet.test.ts tests using the DescriptiveQueryResponse fixture."""

    def test_table_columns(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.table_columns() == [
            {
                "dataIndex": "base_orders.created_at.month",
                "format": None,
                "key": "base_orders.created_at.month",
                "meta": None,
                "currency": None,
                "granularity": "month",
                "shortTitle": "Created at",
                "title": "Base Orders Created at",
                "type": "time",
            },
            {
                "dataIndex": "base_orders.status",
                "format": None,
                "key": "base_orders.status",
                "meta": {"addDesc": "The status of order", "moreNum": 42},
                "currency": None,
                "granularity": None,
                "shortTitle": "Status",
                "title": "Base Orders Status",
                "type": "string",
            },
            {
                "dataIndex": "base_orders.count",
                "format": None,
                "key": "base_orders.count",
                "meta": None,
                "currency": None,
                "granularity": None,
                "shortTitle": "Count",
                "title": "Base Orders Count",
                "type": "number",
            },
        ]

    def test_total_row(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.total_row() == {
            "completed,base_orders.count": 2,
            "processing,base_orders.count": 0,
            "shipped,base_orders.count": 0,
            "x": "2023-04-01T00:00:00.000",
            "xValues": ["2023-04-01T00:00:00.000"],
        }

    def test_pivot_query(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.pivot_query() == DESCRIPTIVE_QUERY_RESPONSE["pivotQuery"]

    def test_total_rows(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.total_rows() == 19

    def test_raw_data(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.raw_data() == DESCRIPTIVE_QUERY_RESPONSE["results"][0]["data"]

    def test_annotation(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.annotation() == DESCRIPTIVE_QUERY_RESPONSE["results"][0]["annotation"]

    def test_categories(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        assert rs.categories() == [
            {
                "completed,base_orders.count": 2,
                "processing,base_orders.count": 0,
                "shipped,base_orders.count": 0,
                "x": "2023-04-01T00:00:00.000",
                "xValues": ["2023-04-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 6,
                "processing,base_orders.count": 6,
                "shipped,base_orders.count": 9,
                "x": "2023-05-01T00:00:00.000",
                "xValues": ["2023-05-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 5,
                "processing,base_orders.count": 5,
                "shipped,base_orders.count": 13,
                "x": "2023-06-01T00:00:00.000",
                "xValues": ["2023-06-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 5,
                "processing,base_orders.count": 7,
                "shipped,base_orders.count": 5,
                "x": "2023-07-01T00:00:00.000",
                "xValues": ["2023-07-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 11,
                "processing,base_orders.count": 3,
                "shipped,base_orders.count": 4,
                "x": "2023-08-01T00:00:00.000",
                "xValues": ["2023-08-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 5,
                "processing,base_orders.count": 10,
                "shipped,base_orders.count": 9,
                "x": "2023-09-01T00:00:00.000",
                "xValues": ["2023-09-01T00:00:00.000"],
            },
            {
                "completed,base_orders.count": 4,
                "processing,base_orders.count": 5,
                "shipped,base_orders.count": 9,
                "x": "2023-10-01T00:00:00.000",
                "xValues": ["2023-10-01T00:00:00.000"],
            },
        ]

    def test_serialize_deserialize(self):
        rs = ResultSet(DESCRIPTIVE_QUERY_RESPONSE)

        serialized = rs.serialize()
        restored = ResultSet.deserialize(serialized)

        assert restored.raw_data() == rs.raw_data()


class TestPivotConfigFillWithValue:
    """Ported from ResultSet.test.ts describe('fill missing dates')/tablePivot
    tests around lines 1580-1771 (fillWithValue option)."""

    def _fill_missing_dates_fixture(self):
        return ResultSet(
            {
                "query": {
                    "measures": ["Orders.total"],
                    "timeDimensions": [
                        {
                            "dimension": "Orders.createdAt",
                            "granularity": "day",
                            "dateRange": ["2020-01-08T00:00:00.000", "2020-01-11T23:59:59.999"],
                        }
                    ],
                    "filters": [],
                    "timezone": "UTC",
                },
                "data": [
                    {"Orders.createdAt": "2020-01-08T00:00:00.000", "Orders.total": 1},
                    {"Orders.createdAt": "2020-01-10T00:00:00.000", "Orders.total": 10},
                ],
                "annotation": {
                    "measures": {},
                    "dimensions": {},
                    "segments": {},
                    "timeDimensions": {
                        "Orders.createdAt": {"title": "Orders Created at", "shortTitle": "Created at", "type": "time"}
                    },
                },
            }
        )

    def test_fill_missing_dates_with_custom_numeric_value(self):
        result_set = self._fill_missing_dates_fixture()

        assert result_set.table_pivot({"fillWithValue": 5}) == [
            {"Orders.createdAt.day": "2020-01-08T00:00:00.000", "Orders.total": 1},
            {"Orders.createdAt.day": "2020-01-09T00:00:00.000", "Orders.total": 5},
            {"Orders.createdAt.day": "2020-01-10T00:00:00.000", "Orders.total": 10},
            {"Orders.createdAt.day": "2020-01-11T00:00:00.000", "Orders.total": 5},
        ]

    def test_fill_missing_dates_with_custom_string(self):
        result_set = self._fill_missing_dates_fixture()

        assert result_set.table_pivot({"fillWithValue": "N/A"}) == [
            {"Orders.createdAt.day": "2020-01-08T00:00:00.000", "Orders.total": 1},
            {"Orders.createdAt.day": "2020-01-09T00:00:00.000", "Orders.total": "N/A"},
            {"Orders.createdAt.day": "2020-01-10T00:00:00.000", "Orders.total": 10},
            {"Orders.createdAt.day": "2020-01-11T00:00:00.000", "Orders.total": "N/A"},
        ]

    def test_fill_with_value_preserves_actual_zero_values(self):
        """Ported from ResultSet.test.ts 'fillWithValue should preserve actual
        zero values (issue #10225)' — also exercises an explicit x/y override."""
        result_set = ResultSet(
            {
                "query": {
                    "measures": ["TestCube.value"],
                    "dimensions": ["TestCube.category", "TestCube.type"],
                    "filters": [],
                    "timezone": "UTC",
                },
                "data": [
                    {"TestCube.category": "A", "TestCube.type": "X", "TestCube.value": 10},
                    {"TestCube.category": "A", "TestCube.type": "Y", "TestCube.value": 0},
                    {"TestCube.category": "B", "TestCube.type": "X", "TestCube.value": 30},
                ],
                "annotation": {
                    "measures": {"TestCube.value": {"title": "Value", "shortTitle": "Value", "type": "number"}},
                    "dimensions": {
                        "TestCube.category": {"title": "Category", "shortTitle": "Category", "type": "string"},
                        "TestCube.type": {"title": "Type", "shortTitle": "Type", "type": "string"},
                    },
                    "segments": {},
                    "timeDimensions": {},
                },
            }
        )

        pivot_config = {"x": ["TestCube.category"], "y": ["TestCube.type", "measures"], "fillWithValue": "-"}

        assert result_set.table_pivot(pivot_config) == [
            {"TestCube.category": "A", "X,TestCube.value": 10, "Y,TestCube.value": 0},
            {"TestCube.category": "B", "X,TestCube.value": 30, "Y,TestCube.value": "-"},
        ]


class TestMergePivotsJoinDateRange:
    """`joinDateRange` has no dedicated JS test in ResultSet.test.ts or
    compare-date-range.test.ts (both existing multi-result suites use the
    default `joinDateRange: false`). This hand-traces the documented
    `mergePivots` algorithm (ResultSet.ts:631-646) against a minimal
    synthetic blendingQuery fixture instead of a transcribed JS assertion.
    """

    def test_join_date_range_true_joins_x_values_across_results(self):
        result_set = ResultSet(
            {
                "queryType": "blendingQuery",
                "results": [
                    {
                        "query": {"measures": ["A.count"], "dimensions": ["Cube.day"], "filters": [], "order": []},
                        "data": [{"Cube.day": "Mon", "A.count": 1}],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {"Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"}},
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                    {
                        "query": {"measures": ["A.count"], "dimensions": ["Cube.day"], "filters": [], "order": []},
                        "data": [{"Cube.day": "Tue", "A.count": 2}],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {"Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"}},
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                ],
                "pivotQuery": {"measures": ["A.count"], "dimensions": ["Cube.day"]},
            }
        )

        assert result_set.pivot({"joinDateRange": True}) == [
            {"xValues": ["Mon, Tue"], "yValuesArray": [[["A.count"], 1], [["A.count"], 2]]}
        ]

    def test_join_date_range_true_with_multi_element_x_values(self):
        """Exercises the inner-`,`-vs-outer-`, `-separator distinction in
        `mergePivots`'s xValues join (ResultSet.ts:637-638), which the
        single-element-xValues test above can't: JS's `Array.prototype.join`
        stringifies each nested `xValues` array with its own default `,`
        separator before the outer `.join(', ')` runs."""
        result_set = ResultSet(
            {
                "queryType": "blendingQuery",
                "results": [
                    {
                        "query": {
                            "measures": ["A.count"],
                            "dimensions": ["Cube.day", "Cube.region"],
                            "filters": [],
                            "order": [],
                        },
                        "data": [{"Cube.day": "Mon", "Cube.region": "US", "A.count": 1}],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {
                                "Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"},
                                "Cube.region": {"title": "Region", "shortTitle": "Region", "type": "string"},
                            },
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                    {
                        "query": {
                            "measures": ["A.count"],
                            "dimensions": ["Cube.day", "Cube.region"],
                            "filters": [],
                            "order": [],
                        },
                        "data": [{"Cube.day": "Tue", "Cube.region": "EU", "A.count": 2}],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {
                                "Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"},
                                "Cube.region": {"title": "Region", "shortTitle": "Region", "type": "string"},
                            },
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                ],
                "pivotQuery": {"measures": ["A.count"], "dimensions": ["Cube.day", "Cube.region"]},
            }
        )

        assert result_set.pivot({"joinDateRange": True}) == [
            {"xValues": ["Mon,US, Tue,EU"], "yValuesArray": [[["A.count"], 1], [["A.count"], 2]]}
        ]

    def test_merge_pivots_with_mismatched_length_results_zips_positionally(self):
        """Not a bug to fix: JS's `mergePivots` (ResultSet.ts:631-646) zips
        results together purely by index, keyed off whichever result has the
        FEWEST rows. When `compareDateRangeQuery`/`blendingQuery` results have
        different row counts, the shorter result's xValues silently "win" the
        label for every merged row, and any extra rows in longer results
        beyond the shorter result's length are silently dropped. This pins
        down (and documents) that behavior so it isn't "fixed" by accident —
        every JS/Python fixture transcribed so far happens to use equal-length
        results, so nothing else exercises this path."""
        result_set = ResultSet(
            {
                "queryType": "blendingQuery",
                "results": [
                    {
                        "query": {
                            "measures": ["A.count"],
                            "dimensions": ["Cube.day"],
                            "filters": [],
                            "order": [],
                        },
                        "data": [
                            {"Cube.day": "Mon", "A.count": 1},
                            {"Cube.day": "Tue", "A.count": 2},
                            {"Cube.day": "Wed", "A.count": 3},
                        ],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {"Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"}},
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                    {
                        "query": {
                            "measures": ["A.count"],
                            "dimensions": ["Cube.day"],
                            "filters": [],
                            "order": [],
                        },
                        "data": [{"Cube.day": "X", "A.count": 100}],
                        "annotation": {
                            "measures": {"A.count": {"title": "A Count", "shortTitle": "Count", "type": "number"}},
                            "dimensions": {"Cube.day": {"title": "Day", "shortTitle": "Day", "type": "string"}},
                            "segments": {},
                            "timeDimensions": {},
                        },
                    },
                ],
                "pivotQuery": {"measures": ["A.count"], "dimensions": ["Cube.day"]},
            }
        )

        assert result_set.pivot() == [
            {"xValues": ["X"], "yValuesArray": [[["A.count"], 1], [["A.count"], 100]]}
        ]
