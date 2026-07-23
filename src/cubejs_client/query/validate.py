"""Port of the non-UI parts of utils.ts: validateQuery, removeEmptyQueryFields,
areQueriesEqual. (defaultHeuristics/movePivotItem are playground/UI helpers and
are out of scope for this SDK.)
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

_ARRAY_FIELDS = ("measures", "dimensions", "segments", "timeDimensions", "filters")


def remove_empty_query_fields(query: Optional[Mapping[str, Any]]) -> dict:
    query = query or {}
    result: dict = {}
    for key, value in query.items():
        if key in _ARRAY_FIELDS and isinstance(value, list) and len(value) == 0:
            continue
        if key == "order" and value is not None:
            if isinstance(value, list) and len(value) == 0:
                continue
            if isinstance(value, dict) and len(value) == 0:
                continue
        result[key] = value
    return result


def validate_query(query: Optional[Mapping[str, Any]]) -> dict:
    query = query or {}
    return remove_empty_query_fields(
        {
            **query,
            "filters": [f for f in (query.get("filters") or []) if "operator" in f],
            "timeDimensions": [
                td for td in (query.get("timeDimensions") or []) if td.get("dateRange") or td.get("granularity")
            ],
        }
    )


def are_queries_equal(query1: Optional[Mapping[str, Any]], query2: Optional[Mapping[str, Any]]) -> bool:
    order1 = list(((query1 or {}).get("order") or {}).items())
    order2 = list(((query2 or {}).get("order") or {}).items())
    return order1 == order2 and query1 == query2
