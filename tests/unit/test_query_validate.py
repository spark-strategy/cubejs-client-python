"""Tests for query/validate.py, ported behavior from utils.ts's
removeEmptyQueryFields/validateQuery/areQueriesEqual."""

from cubejs_client import are_queries_equal, remove_empty_query_fields, validate_query


def test_remove_empty_query_fields_drops_empty_arrays_and_order():
    query = {
        "measures": ["Orders.count"],
        "dimensions": [],
        "filters": [],
        "order": {},
        "timezone": "UTC",
    }

    assert remove_empty_query_fields(query) == {"measures": ["Orders.count"], "timezone": "UTC"}


def test_remove_empty_query_fields_keeps_non_empty_order():
    query = {"measures": ["Orders.count"], "order": {"Orders.count": "desc"}}

    assert remove_empty_query_fields(query) == query


def test_remove_empty_query_fields_handles_none_query():
    assert remove_empty_query_fields(None) == {}


def test_validate_query_drops_filters_without_operator():
    query = {
        "measures": ["Orders.count"],
        "filters": [
            {"member": "Orders.status", "operator": "equals", "values": ["completed"]},
            {"member": "Orders.status", "values": ["completed"]},  # missing operator
        ],
    }

    result = validate_query(query)

    assert result["filters"] == [{"member": "Orders.status", "operator": "equals", "values": ["completed"]}]


def test_validate_query_drops_time_dimensions_without_date_range_or_granularity():
    query = {
        "measures": ["Orders.count"],
        "timeDimensions": [
            {"dimension": "Orders.createdAt", "granularity": "month"},
            {"dimension": "Orders.completedAt"},  # neither dateRange nor granularity
            {"dimension": "Orders.shippedAt", "dateRange": ["2020-01-01", "2020-12-31"]},
        ],
    }

    result = validate_query(query)

    assert result["timeDimensions"] == [
        {"dimension": "Orders.createdAt", "granularity": "month"},
        {"dimension": "Orders.shippedAt", "dateRange": ["2020-01-01", "2020-12-31"]},
    ]


def test_are_queries_equal_true_for_structurally_identical_queries():
    q1 = {"measures": ["Orders.count"], "order": {"Orders.count": "desc"}}
    q2 = {"measures": ["Orders.count"], "order": {"Orders.count": "desc"}}

    assert are_queries_equal(q1, q2) is True


def test_are_queries_equal_false_for_different_order():
    q1 = {"measures": ["Orders.count"], "order": {"Orders.count": "desc"}}
    q2 = {"measures": ["Orders.count"], "order": {"Orders.count": "asc"}}

    assert are_queries_equal(q1, q2) is False


def test_are_queries_equal_handles_none():
    assert are_queries_equal(None, None) is True
    assert are_queries_equal(None, {"measures": ["Orders.count"]}) is False
