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
        assert restored.table_columns() == rs.table_columns()
