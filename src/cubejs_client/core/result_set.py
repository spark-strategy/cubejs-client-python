"""Port of ResultSet.ts, including compareDateRangeQuery/blendingQuery support.

This is a faithful, method-for-method port of the JS `ResultSet` class:
`pivot`/`chart_pivot`/`table_pivot`/`table_columns`/`series`/`series_names`
all handle multi-result (`compareDateRangeQuery`/`blendingQuery`) load
responses via `_merge_pivots`, mirroring JS's private `mergePivots`.
`decompose()` splits a multi-result `ResultSet` back into one regularQuery
`ResultSet` per result. `query()`/`raw_data()`/`annotation()` remain
regularQuery-only, per JS (`decompose()` first if you need those on a
compare/blending result).
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .alias import alias_series
from .js_compat import js_array_join, js_parse_float, merge_deep_left, uniq_preserve_order
from .pivot_config import get_normalized_pivot_config, time_dimension_member
from .time_series import (
    DateRegex,
    LocalDateRegex,
    TIME_SERIES,
    day_range,
    is_predefined_granularity,
    parse_datetime,
)

QUERY_TYPE_REGULAR = "regularQuery"
QUERY_TYPE_COMPARE_DATE_RANGE = "compareDateRangeQuery"
QUERY_TYPE_BLENDING = "blendingQuery"

_QUERY_TYPES = {QUERY_TYPE_REGULAR, QUERY_TYPE_COMPARE_DATE_RANGE, QUERY_TYPE_BLENDING}


def _measure_from_axis(axis_values: Sequence[Any]) -> Any:
    # Mirrors JS `axisValues[axisValues.length - 1]`, which yields `undefined`
    # (not a thrown error) when axisValues is empty.
    return axis_values[-1] if axis_values else None


class ResultSet:
    @staticmethod
    def measure_from_axis(axis_values: Sequence[Any]) -> Any:
        return _measure_from_axis(axis_values)

    @staticmethod
    def time_dimension_member(td: Mapping[str, Any]) -> str:
        return time_dimension_member(td)

    @staticmethod
    def get_normalized_pivot_config(
        query: Optional[Mapping[str, Any]] = None, pivot_config: Optional[Mapping[str, Any]] = None
    ) -> dict:
        return get_normalized_pivot_config(query, pivot_config)

    @classmethod
    def deserialize(cls, data: Mapping[str, Any], options: Optional[dict] = None) -> "ResultSet":
        return cls(data["loadResponse"], options)

    def __init__(self, load_response: Mapping[str, Any], options: Optional[dict] = None):
        options = options or {}

        if "queryType" in load_response and load_response.get("queryType") is not None:
            self.load_response: dict = dict(load_response)
            self.query_type: str = load_response["queryType"]
            self.load_responses: List[dict] = list(load_response["results"])
        else:
            self.query_type = QUERY_TYPE_REGULAR
            self.load_response = {
                **load_response,
                "pivotQuery": {**load_response.get("query", {}), "queryType": self.query_type},
            }
            self.load_responses = [dict(load_response)]

        if self.query_type not in _QUERY_TYPES:
            raise ValueError("Unknown query type")

        self.parse_date_measures: bool = bool(options.get("parseDateMeasures"))
        self.options = options
        self._backward_compatible_data: Dict[int, list] = {}

    # -- axis helpers --------------------------------------------------

    def _axis_values(self, axis: Sequence[str], result_index: int = 0):
        query = self.load_responses[result_index]["query"]
        axis_without_measures = [d for d in axis if d != "measures"]
        measures = (query.get("measures") or []) if "measures" in axis else []

        def compute(row: Mapping[str, Any]):
            def value(measure: Optional[str] = None):
                result = [row[d] if row.get(d) is not None else None for d in axis_without_measures]
                if measure is not None:
                    result.append(measure)
                return result

            if measures:
                return [value(m) for m in measures]
            return [value()]

        return compute

    def _axis_values_string(self, axis_values: Sequence[Any], delimiter: str = ", ") -> str:
        def fmt(v: Any) -> str:
            if v is None:
                return "∅"
            if v == "":
                return "[Empty string]"
            return str(v)

        return delimiter.join(fmt(v) for v in axis_values)

    def normalize_pivot_config(self, pivot_config: Optional[dict] = None) -> dict:
        return get_normalized_pivot_config(self.load_response.get("pivotQuery"), pivot_config)

    def _time_dimension_backward_compatible_data(self, result_index: int) -> list:
        if result_index not in self._backward_compatible_data:
            data = self.load_responses[result_index]["data"]
            query = self.load_responses[result_index]["query"]
            time_dimensions = [td for td in (query.get("timeDimensions") or []) if td.get("granularity")]

            def enrich(row: Mapping[str, Any]) -> dict:
                extra = {}
                for field in row.keys():
                    found_td = next((td for td in time_dimensions if td["dimension"] == field), None)
                    if found_td:
                        member = time_dimension_member(found_td)
                        if not row.get(member):
                            extra[member] = row[field]
                return {**row, **extra}

            self._backward_compatible_data[result_index] = [enrich(row) for row in data]
        return self._backward_compatible_data[result_index]

    # -- time series -----------------------------------------------------

    def time_series(
        self,
        time_dimension: Mapping[str, Any],
        result_index: Optional[int] = None,
        annotations: Optional[Mapping[str, Any]] = None,
    ):
        granularity = time_dimension.get("granularity")
        if not granularity:
            return None

        date_range = time_dimension.get("dateRange")
        if not date_range:
            member = time_dimension_member(time_dimension)
            raw_rows = self._time_dimension_backward_compatible_data(result_index or 0)
            dates = []
            for row in raw_rows:
                value = row.get(member)
                if value:
                    dates.append(parse_datetime(value))
            date_range = [min(dates), max(dates)] if dates else None

        if not date_range:
            return None

        explicit_date_range = time_dimension.get("dateRange")
        if explicit_date_range:
            pad_to_day = any(DateRegex.match(str(d)) for d in explicit_date_range)
        else:
            pad_to_day = granularity not in ("hour", "minute", "second")

        start, end = date_range[0], date_range[1]
        rng = day_range(start, end)

        if is_predefined_granularity(granularity):
            effective_range = rng.snap_to("day") if pad_to_day else rng
            return TIME_SERIES[granularity](effective_range)

        raise NotImplementedError(
            f'Granularity "{granularity}" not found in time dimension '
            f'"{time_dimension.get("dimension")}" (custom granularities are not supported yet)'
        )

    # -- pivot -----------------------------------------------------------

    def pivot(self, pivot_config: Optional[dict] = None) -> list:
        normalized = self.normalize_pivot_config(pivot_config)
        query = self.load_response["pivotQuery"]

        def pivot_impl(result_index: int = 0) -> list:
            def measure_value(row: Mapping[str, Any], measure: Any) -> Any:
                v = row.get(measure)
                if v is not None:
                    return v
                fill_with_value = normalized.get("fillWithValue")
                if fill_with_value is not None:
                    return fill_with_value
                return 0

            def group_by_x_axis_default(items: list) -> list:
                acc: Dict[str, list] = {}
                for item in items:
                    key = self._axis_values_string(item["xValues"])
                    acc.setdefault(key, []).append(item)
                return list(acc.items())

            group_by_x_axis = group_by_x_axis_default

            time_dims_with_granularity = [
                td for td in (query.get("timeDimensions") or []) if td.get("granularity")
            ]
            expected_x = [time_dimension_member(td) for td in time_dims_with_granularity]

            if (
                normalized.get("fillMissingDates")
                and len(normalized["x"]) == 1
                and normalized["x"] == expected_x
            ):
                series_list = [
                    self.time_series(
                        lr["query"]["timeDimensions"][0], result_index, lr["annotation"]["timeDimensions"]
                    )
                    for lr in self.load_responses
                ]

                if series_list and series_list[0] is not None:
                    series = series_list[result_index]

                    def group_by_x_axis_series(items: list) -> list:
                        by_x_values: Dict[Any, list] = {}
                        for item in items:
                            by_x_values.setdefault(item["xValues"][0], []).append(item)
                        return [
                            (d, by_x_values.get(d, [{"xValues": [d], "row": {}}])) for d in series
                        ]

                    group_by_x_axis = group_by_x_axis_series

            x_axis_values = self._axis_values(normalized["x"], result_index)
            y_axis_values = self._axis_values(normalized["y"], result_index)

            expanded = []
            for row in self._time_dimension_backward_compatible_data(result_index):
                for x_values in x_axis_values(row):
                    expanded.append({"xValues": x_values, "row": row})

            x_grouped = group_by_x_axis(expanded)

            y_values_map: Dict[str, list] = {}
            for _, items in x_grouped:
                for item in items:
                    row = item["row"]
                    if len(row) > 0:
                        for values in y_axis_values(row):
                            y_values_map[js_array_join(values)] = values
            all_y_values = list(y_values_map.values())

            measure_on_x = "measures" in normalized["x"]

            result = []
            for _, items in x_grouped:
                x_values = items[0]["xValues"]
                y_grouped: Dict[str, dict] = {}
                for item in items:
                    row = item["row"]
                    for y_values in y_axis_values(row):
                        y_grouped[self._axis_values_string(y_values)] = {"yValues": y_values, "row": row}

                y_values_array = []
                for y_values in all_y_values:
                    measure = _measure_from_axis(x_values) if measure_on_x else _measure_from_axis(y_values)
                    matched = y_grouped.get(self._axis_values_string(y_values), {"row": {}})
                    y_values_array.append([y_values, measure_value(matched["row"], measure)])

                result.append({"xValues": x_values, "yValuesArray": y_values_array})

            return result

        if len(self.load_responses) > 1:
            pivots = [pivot_impl(index) for index in range(len(self.load_responses))]
            return self._merge_pivots(pivots, normalized.get("joinDateRange") or False)

        return pivot_impl()

    def _merge_pivots(self, pivots: List[list], join_date_range: bool) -> list:
        min_length_pivot: Optional[List[dict]] = None
        for current in pivots:
            if min_length_pivot is not None and len(current) >= len(min_length_pivot):
                continue
            min_length_pivot = current
        min_length_pivot = min_length_pivot or []

        result = []
        for index in range(len(min_length_pivot)):
            if join_date_range:
                x_values = [
                    ", ".join(
                        js_array_join(pivot[index]["xValues"] if index < len(pivot) else [], ",")
                        for pivot in pivots
                    )
                ]
            else:
                x_values = min_length_pivot[index]["xValues"]

            y_values_array: list = []
            for pivot in pivots:
                y_values_array.extend(pivot[index]["yValuesArray"])

            result.append({"xValues": x_values, "yValuesArray": y_values_array})
        return result

    # -- chart / table shapes --------------------------------------------

    def chart_pivot(self, pivot_config: Optional[dict] = None) -> list:
        def validate(value: Any) -> Any:
            s = str(value)
            if self.parse_date_measures and LocalDateRegex.match(s):
                return parse_datetime(s)
            f = js_parse_float(s)
            if not math.isnan(f):
                return f
            return value

        duplicate_measures: set = set()
        if self.query_type == QUERY_TYPE_BLENDING:
            all_measures = [m for lr in self.load_responses for m in (lr["query"].get("measures") or [])]
            seen: set = set()
            for m in all_measures:
                if m in seen:
                    duplicate_measures.add(m)
                seen.add(m)

        result = []
        for row in self.pivot(pivot_config):
            y_values_map: dict = {}
            for i, (y_values, m) in enumerate(row["yValuesArray"]):
                key = self._axis_values_string(alias_series(y_values, i, pivot_config, duplicate_measures), ",")
                y_values_map[key] = validate(m) if m else m

            chart_row = {"x": self._axis_values_string(row["xValues"], ","), "xValues": row["xValues"]}
            chart_row.update(y_values_map)
            result.append(chart_row)
        return result

    def table_pivot(self, pivot_config: Optional[dict] = None) -> list:
        effective = pivot_config if pivot_config is not None else {}
        normalized = self.normalize_pivot_config(effective)
        is_measures_present = "measures" in (normalized["x"] + normalized["y"])

        result = []
        for row in self.pivot(normalized):
            pairs: List[tuple] = []
            for index, key in enumerate(normalized["x"]):
                pairs.append((key, row["xValues"][index] if index < len(row["xValues"]) else None))
            if is_measures_present:
                for y_values, measure in row["yValuesArray"]:
                    key = js_array_join(y_values) if y_values else "value"
                    pairs.append((key, measure))
            result.append(dict(pairs))
        return result

    def table_columns(self, pivot_config: Optional[dict] = None) -> list:
        effective = pivot_config if pivot_config is not None else {}
        normalized = self.normalize_pivot_config(effective)

        annotations: dict = {"dimensions": {}, "measures": {}, "timeDimensions": {}, "segments": {}}
        for lr in self.load_responses:
            annotations = merge_deep_left(annotations, lr["annotation"])

        flat_meta: dict = {}
        for section in annotations.values():
            flat_meta.update(section)

        def extract_fields(key: str) -> dict:
            meta_entry = flat_meta.get(key) or {}
            granularity = meta_entry.get("granularity")
            return {
                "key": key,
                "title": meta_entry.get("title"),
                "shortTitle": meta_entry.get("shortTitle"),
                "type": meta_entry.get("type"),
                "format": meta_entry.get("format"),
                "meta": meta_entry.get("meta"),
                "currency": meta_entry.get("currency"),
                "granularity": granularity.get("name") if granularity else None,
            }

        pivot_rows = self.pivot(normalized)

        schema: dict = {}
        first_y_values_array = pivot_rows[0]["yValuesArray"] if pivot_rows else []
        for y_values, _ in first_y_values_array:
            if len(y_values) > 0:
                current_item = schema
                for index, value in enumerate(y_values):
                    node_key = f"_{value}"
                    existing_children = current_item.get(node_key, {}).get("children", {})
                    member_id = value if normalized["y"][index] == "measures" else normalized["y"][index]
                    current_item[node_key] = {"key": value, "memberId": member_id, "children": existing_children}
                    current_item = current_item[node_key]["children"]

        def to_columns(item: dict, path: Optional[list] = None) -> list:
            path = path or []
            if not item:
                return []
            columns = []
            for node in item.values():
                key = node["key"]
                member_id = node["memberId"]
                children = to_columns(node["children"], [*path, key])
                fields = extract_fields(member_id)
                title = fields.pop("title")
                short_title = fields.pop("shortTitle")
                dimension_value = key if (key != member_id or title is None) else ""
                joined_title = js_array_join([title, dimension_value], " ").strip()

                if not children:
                    columns.append(
                        {
                            **fields,
                            "key": key,
                            "dataIndex": js_array_join([*path, key]),
                            "title": joined_title,
                            "shortTitle": dimension_value or short_title,
                        }
                    )
                else:
                    columns.append(
                        {
                            **fields,
                            "key": key,
                            "title": joined_title,
                            "shortTitle": dimension_value or short_title,
                            "children": children,
                        }
                    )
            return columns

        other_columns: list = []
        if not pivot_rows and "measures" in normalized["y"]:
            measures = self.load_responses[0]["query"].get("measures") or []
            other_columns = [{**extract_fields(key), "dataIndex": key} for key in measures]

        if not normalized["y"] and "measures" in normalized["x"]:
            other_columns.append(
                {"key": "value", "dataIndex": "value", "title": "Value", "shortTitle": "Value", "type": "string"}
            )

        columns = []
        for key in normalized["x"]:
            if key == "measures":
                columns.append(
                    {
                        "key": "measures",
                        "dataIndex": "measures",
                        "title": "Measures",
                        "shortTitle": "Measures",
                        "type": "string",
                    }
                )
            else:
                columns.append({**extract_fields(key), "dataIndex": key})

        return columns + to_columns(schema) + other_columns

    def total_row(self, pivot_config: Optional[dict] = None):
        rows = self.chart_pivot(pivot_config)
        return rows[0] if rows else None

    def categories(self, pivot_config: Optional[dict] = None) -> list:
        return self.chart_pivot(pivot_config)

    def series(self, pivot_config: Optional[dict] = None) -> list:
        names = self.series_names(pivot_config)
        chart_rows = self.chart_pivot(pivot_config)
        return [
            {
                "title": entry["title"],
                "shortTitle": entry["shortTitle"],
                "key": entry["key"],
                "series": [{"value": row.get(entry["key"]), "x": row["x"]} for row in chart_rows],
            }
            for entry in names
        ]

    def series_names(self, pivot_config: Optional[dict] = None) -> list:
        normalized = self.normalize_pivot_config(pivot_config)
        measures: dict = {}
        for lr in self.load_responses:
            measures.update(lr["annotation"].get("measures") or {})

        series_names: list = []
        for index in range(len(self.load_responses)):
            axis_fn = self._axis_values(normalized["y"], index)
            flattened = []
            for row in self._time_dimension_backward_compatible_data(index):
                flattened.extend(axis_fn(row))
            series_names.extend(uniq_preserve_order(flattened))

        duplicate_measures: set = set()
        if self.query_type == QUERY_TYPE_BLENDING:
            all_measures = [m for lr in self.load_responses for m in (lr["query"].get("measures") or [])]
            seen: set = set()
            for m in all_measures:
                if m in seen:
                    duplicate_measures.add(m)
                seen.add(m)

        has_measures_in_y = "measures" in normalized["y"]
        result = []
        for i, axis_values in enumerate(series_names):
            aliased = alias_series(axis_values, i, normalized, duplicate_measures)
            if has_measures_in_y:
                measure_key = _measure_from_axis(axis_values)
                title_parts = aliased[:-1] + [measures[measure_key]["title"]]
                short_title_parts = aliased[:-1] + [measures[measure_key]["shortTitle"]]
            else:
                title_parts = aliased
                short_title_parts = aliased

            result.append(
                {
                    "title": self._axis_values_string(title_parts, ", "),
                    "shortTitle": self._axis_values_string(short_title_parts, ", "),
                    "key": self._axis_values_string(aliased, ","),
                    "yValues": axis_values,
                }
            )
        return result

    # -- regularQuery-only accessors --------------------------------------

    def _require_regular_query(self) -> None:
        if self.query_type != QUERY_TYPE_REGULAR:
            raise ValueError(
                f"Method is not supported for a '{self.query_type}' query type. Please use decompose"
            )

    def query(self) -> dict:
        self._require_regular_query()
        return self.load_responses[0]["query"]

    def pivot_query(self) -> Optional[dict]:
        return self.load_response.get("pivotQuery")

    def total_rows(self):
        return self.load_responses[0].get("total")

    def decompose(self) -> List["ResultSet"]:
        return [
            ResultSet(
                {
                    "queryType": QUERY_TYPE_REGULAR,
                    "pivotQuery": {**result["query"], "queryType": QUERY_TYPE_REGULAR},
                    "results": [result],
                },
                self.options,
            )
            for result in self.load_responses
        ]

    def raw_data(self) -> list:
        self._require_regular_query()
        return self.load_responses[0]["data"]

    def annotation(self) -> dict:
        self._require_regular_query()
        return self.load_responses[0]["annotation"]

    def serialize(self) -> dict:
        return {"loadResponse": copy.deepcopy(self.load_response)}
