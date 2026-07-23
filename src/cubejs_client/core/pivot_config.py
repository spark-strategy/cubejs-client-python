"""Port of ResultSet.getNormalizedPivotConfig (src/ResultSet.ts:375-439)."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .js_compat import merge_deep_left


def time_dimension_member(td: Mapping[str, Any]) -> str:
    return f"{td['dimension']}.{td['granularity']}"


def get_normalized_pivot_config(
    query: Optional[Mapping[str, Any]], pivot_config: Optional[Mapping[str, Any]] = None
) -> dict:
    if pivot_config is not None and not isinstance(pivot_config, Mapping):
        raise TypeError(
            f"pivot_config must be a dict or None, got {type(pivot_config).__name__}. "
            "If you built one with the PivotConfig builder, call `.build()` first."
        )

    default_pivot_config = {"x": [], "y": [], "fillMissingDates": True, "joinDateRange": False}

    query = query or {}
    measures = query.get("measures") or []
    dimensions = query.get("dimensions") or []
    time_dimensions = [td for td in (query.get("timeDimensions") or []) if td.get("granularity")]

    # NOTE: `pivot_config is None` mirrors JS `pivotConfig || (...)`, which only
    # falls through here when the caller passed undefined/None. An explicit `{}`
    # (as tablePivot/tableColumns pass when called with no args) is truthy in JS
    # and must NOT trigger this default — unlike Python's `{} or ...`.
    if pivot_config is None:
        if time_dimensions:
            pivot_config = {
                "x": [time_dimension_member(td) for td in time_dimensions],
                "y": list(dimensions),
            }
        else:
            pivot_config = {"x": list(dimensions), "y": []}

    normalized = merge_deep_left(pivot_config, default_pivot_config)

    def substitute_time_dimension_members(axis: list) -> list:
        result = []
        for sub_dim in axis:
            matching_td = next((td for td in time_dimensions if td["dimension"] == sub_dim), None)
            if matching_td and sub_dim not in dimensions:
                result.append(time_dimension_member(matching_td))
            else:
                result.append(sub_dim)
        return result

    normalized["x"] = substitute_time_dimension_members(normalized["x"])
    normalized["y"] = substitute_time_dimension_members(normalized["y"])

    all_included_dimensions = normalized["x"] + normalized["y"]
    all_dimensions = [time_dimension_member(td) for td in time_dimensions] + list(dimensions)

    def dimension_filter(key: str) -> bool:
        return key in all_dimensions or key == "measures"

    normalized["x"] = [
        d
        for d in normalized["x"]
        + [d for d in all_dimensions if d not in all_included_dimensions and d != "compareDateRange"]
        if dimension_filter(d)
    ]
    normalized["y"] = [d for d in normalized["y"] if dimension_filter(d)]

    if "measures" not in normalized["x"] + normalized["y"]:
        normalized["y"].append("measures")

    if "compareDateRange" in dimensions and "compareDateRange" not in normalized["y"] + normalized["x"]:
        normalized["y"].insert(0, "compareDateRange")

    if not measures:
        normalized["x"] = [d for d in normalized["x"] if d != "measures"]
        normalized["y"] = [d for d in normalized["y"] if d != "measures"]

    return normalized
