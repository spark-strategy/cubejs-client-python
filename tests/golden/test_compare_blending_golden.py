"""Golden tests for compareDateRangeQuery/blendingQuery, ported verbatim from
compare-date-range.test.ts and data-blending.test.ts in the JS SDK.
"""

from cubejs_client.core.result_set import ResultSet

from .fixtures_compare_blending import (
    BLENDING_LOAD_RESPONSE,
    BLENDING_LOAD_RESPONSE_WITHOUT_DATE_RANGE,
    COMPARE_DATE_RANGE_LOAD_RESPONSES,
    SINGLE_MEASURE_BLENDING_LOAD_RESPONSE,
)


class TestCompareDateRange:
    """Ported from compare-date-range.test.ts."""

    def test_series_names_and_series_single_time_dimension(self):
        result_set1 = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[0])

        assert result_set1.series_names() == [
            {
                "key": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count",
                "title": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999, Orders Count",
                "shortTitle": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999, Count",
                "yValues": ["2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999", "Orders.count"],
            },
            {
                "key": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count",
                "title": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999, Orders Count",
                "shortTitle": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999, Count",
                "yValues": ["2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999", "Orders.count"],
            },
        ]

        assert result_set1.series() == [
            {
                "key": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count",
                "title": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999, Orders Count",
                "shortTitle": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999, Count",
                "series": [
                    {"value": 1, "x": "2020-08-10T00:00:00.000"},
                    {"value": 0, "x": "2020-08-11T00:00:00.000"},
                    {"value": 1, "x": "2020-08-12T00:00:00.000"},
                    {"value": 0, "x": "2020-08-13T00:00:00.000"},
                    {"value": 0, "x": "2020-08-14T00:00:00.000"},
                    {"value": 0, "x": "2020-08-15T00:00:00.000"},
                    {"value": 0, "x": "2020-08-16T00:00:00.000"},
                ],
            },
            {
                "key": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count",
                "title": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999, Orders Count",
                "shortTitle": "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999, Count",
                "series": [
                    {"value": 2, "x": "2020-08-10T00:00:00.000"},
                    {"value": 1, "x": "2020-08-11T00:00:00.000"},
                    {"value": 0, "x": "2020-08-12T00:00:00.000"},
                    {"value": 1, "x": "2020-08-13T00:00:00.000"},
                    {"value": 0, "x": "2020-08-14T00:00:00.000"},
                    {"value": 1, "x": "2020-08-15T00:00:00.000"},
                    {"value": 0, "x": "2020-08-16T00:00:00.000"},
                ],
            },
        ]

    def test_chart_pivot_single_time_dimension(self):
        result_set1 = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[0])

        assert result_set1.chart_pivot() == [
            {
                "x": "2020-08-10T00:00:00.000",
                "xValues": ["2020-08-10T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 2,
            },
            {
                "x": "2020-08-11T00:00:00.000",
                "xValues": ["2020-08-11T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "x": "2020-08-12T00:00:00.000",
                "xValues": ["2020-08-12T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
            {
                "x": "2020-08-13T00:00:00.000",
                "xValues": ["2020-08-13T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "x": "2020-08-14T00:00:00.000",
                "xValues": ["2020-08-14T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
            {
                "x": "2020-08-15T00:00:00.000",
                "xValues": ["2020-08-15T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "x": "2020-08-16T00:00:00.000",
                "xValues": ["2020-08-16T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
        ]

    def test_chart_pivot_two_dimensions(self):
        result_set2 = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[1])

        assert result_set2.chart_pivot() == [
            {
                "x": "2020-08-10T00:00:00.000",
                "xValues": ["2020-08-10T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 1,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 2,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "x": "2020-08-11T00:00:00.000",
                "xValues": ["2020-08-11T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "x": "2020-08-12T00:00:00.000",
                "xValues": ["2020-08-12T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "x": "2020-08-13T00:00:00.000",
                "xValues": ["2020-08-13T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 1,
            },
            {
                "x": "2020-08-14T00:00:00.000",
                "xValues": ["2020-08-14T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "x": "2020-08-15T00:00:00.000",
                "xValues": ["2020-08-15T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "x": "2020-08-16T00:00:00.000",
                "xValues": ["2020-08-16T00:00:00.000"],
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
        ]

    def test_table_pivot_and_table_columns_single_time_dimension(self):
        result_set1 = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[0])
        pivot_config = {"x": ["Orders.ts.day"], "y": ["compareDateRange", "measures"]}

        columns = result_set1.table_columns(pivot_config)
        assert columns[0]["key"] == "Orders.ts.day"
        assert columns[0]["title"] == "Orders Ts"
        assert columns[0]["shortTitle"] == "Ts"
        assert columns[0]["type"] == "time"
        assert columns[0]["dataIndex"] == "Orders.ts.day"

        assert columns[1]["key"] == "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999"
        assert columns[1]["title"] == "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999"
        assert columns[1]["shortTitle"] == "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999"
        assert columns[1]["children"] == [
            {
                "key": "Orders.count",
                "type": "number",
                "dataIndex": "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count",
                "title": "Orders Count",
                "shortTitle": "Count",
                "format": None,
                "meta": None,
                "currency": None,
                "granularity": None,
            }
        ]

        assert columns[2]["key"] == "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999"
        assert columns[2]["children"][0]["dataIndex"] == "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count"

        assert result_set1.table_pivot(pivot_config) == [
            {
                "Orders.ts.day": "2020-08-10T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 2,
            },
            {
                "Orders.ts.day": "2020-08-11T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "Orders.ts.day": "2020-08-12T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-13T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "Orders.ts.day": "2020-08-14T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-15T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 1,
            },
            {
                "Orders.ts.day": "2020-08-16T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Orders.count": 0,
            },
        ]

    def test_table_pivot_two_dimensions(self):
        result_set2 = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[1])
        pivot_config = {"x": ["Orders.ts.day"], "y": ["compareDateRange", "Users.country", "measures"]}

        assert result_set2.table_pivot(pivot_config) == [
            {
                "Orders.ts.day": "2020-08-10T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 1,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 2,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-11T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-12T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-13T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 1,
            },
            {
                "Orders.ts.day": "2020-08-14T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-15T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 1,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
            {
                "Orders.ts.day": "2020-08-16T00:00:00.000",
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,US,Orders.count": 0,
                "2020-08-10T00:00:00.000 - 2020-08-16T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,Australia,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,France,Orders.count": 0,
                "2020-08-03T00:00:00.000 - 2020-08-09T23:59:59.999,US,Orders.count": 0,
            },
        ]


class TestDataBlending:
    """Ported from data-blending.test.ts."""

    def test_normalized_pivot_config_with_different_dimensions(self):
        result_set1 = ResultSet(BLENDING_LOAD_RESPONSE)
        assert result_set1.normalize_pivot_config() == {
            "x": ["time.day"],
            "y": ["Users.country", "measures"],
            "fillMissingDates": True,
            "joinDateRange": False,
        }

    def test_pivot_with_different_dimensions(self):
        result_set1 = ResultSet(BLENDING_LOAD_RESPONSE)

        assert result_set1.pivot() == [
            {
                "xValues": ["2020-08-01T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 1],
                    [["Australia", "Users.count"], 20],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
            {
                "xValues": ["2020-08-02T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 2],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
            {
                "xValues": ["2020-08-03T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 0],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
            {
                "xValues": ["2020-08-04T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 0],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
            {
                "xValues": ["2020-08-05T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 0],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 34],
                    [["Italy", "Users.count"], 18],
                ],
            },
            {
                "xValues": ["2020-08-06T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 0],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
            {
                "xValues": ["2020-08-07T00:00:00.000"],
                "yValuesArray": [
                    [[None, "Orders.count"], 0],
                    [["Australia", "Users.count"], 0],
                    [["Spain", "Users.count"], 0],
                    [["Italy", "Users.count"], 0],
                ],
            },
        ]

    def test_chart_pivot_query_with_single_measure(self):
        result_set = ResultSet(SINGLE_MEASURE_BLENDING_LOAD_RESPONSE)

        assert result_set.chart_pivot() == [
            {"x": "2020-07-01T00:00:00.000", "0,Users.count": 0, "1,Users.count": 0, "xValues": ["2020-07-01T00:00:00.000"]},
            {"x": "2020-08-01T00:00:00.000", "0,Users.count": 14, "1,Users.count": 2, "xValues": ["2020-08-01T00:00:00.000"]},
            {"x": "2020-09-01T00:00:00.000", "0,Users.count": 23, "1,Users.count": 4, "xValues": ["2020-09-01T00:00:00.000"]},
            {"x": "2020-10-01T00:00:00.000", "0,Users.count": 0, "1,Users.count": 7, "xValues": ["2020-10-01T00:00:00.000"]},
            {"x": "2020-11-01T00:00:00.000", "0,Users.count": 0, "1,Users.count": 0, "xValues": ["2020-11-01T00:00:00.000"]},
        ]

    def test_chart_pivot_query_without_date_range(self):
        result_set = ResultSet(BLENDING_LOAD_RESPONSE_WITHOUT_DATE_RANGE)

        assert result_set.chart_pivot() == [
            {
                "x": "2020-08-01T00:00:00.000",
                "xValues": ["2020-08-01T00:00:00.000"],
                "Orders.count": 1,
                "Australia,Users.count": 20,
                "Italy,Users.count": 0,
                "Spain,Users.count": 0,
            },
            {
                "x": "2020-08-02T00:00:00.000",
                "xValues": ["2020-08-02T00:00:00.000"],
                "Orders.count": 2,
                "Australia,Users.count": 0,
                "Spain,Users.count": 34,
                "Italy,Users.count": 18,
            },
        ]

    def test_chart_pivot_query_with_custom_series_alias(self):
        result_set = ResultSet(SINGLE_MEASURE_BLENDING_LOAD_RESPONSE)

        assert result_set.chart_pivot({"aliasSeries": ["one", "two"]}) == [
            {"x": "2020-07-01T00:00:00.000", "one,Users.count": 0, "two,Users.count": 0, "xValues": ["2020-07-01T00:00:00.000"]},
            {"x": "2020-08-01T00:00:00.000", "one,Users.count": 14, "two,Users.count": 2, "xValues": ["2020-08-01T00:00:00.000"]},
            {"x": "2020-09-01T00:00:00.000", "one,Users.count": 23, "two,Users.count": 4, "xValues": ["2020-09-01T00:00:00.000"]},
            {"x": "2020-10-01T00:00:00.000", "one,Users.count": 0, "two,Users.count": 7, "xValues": ["2020-10-01T00:00:00.000"]},
            {"x": "2020-11-01T00:00:00.000", "one,Users.count": 0, "two,Users.count": 0, "xValues": ["2020-11-01T00:00:00.000"]},
        ]


class TestDecompose:
    """`decompose()` has no direct JS test coverage in these files, but the
    docstring example (ResultSet.ts:1170-1187) demonstrates the expected
    shape: one regularQuery ResultSet per result, each usable with
    raw_data()/query()/annotation()."""

    def test_decompose_compare_date_range(self):
        result_set = ResultSet(COMPARE_DATE_RANGE_LOAD_RESPONSES[0])
        decomposed = result_set.decompose()

        assert len(decomposed) == 2
        assert all(rs.query_type == "regularQuery" for rs in decomposed)
        assert decomposed[0].raw_data() == COMPARE_DATE_RANGE_LOAD_RESPONSES[0]["results"][0]["data"]
        assert decomposed[1].raw_data() == COMPARE_DATE_RANGE_LOAD_RESPONSES[0]["results"][1]["data"]
        assert decomposed[0].query()["timeDimensions"][0]["dateRange"] == [
            "2020-08-10T00:00:00.000",
            "2020-08-16T23:59:59.999",
        ]
