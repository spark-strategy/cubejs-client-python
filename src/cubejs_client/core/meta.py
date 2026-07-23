"""Port of Meta.ts."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Union

_OPERATORS: Dict[str, List[dict]] = {
    "string": [
        {"name": "contains", "title": "contains"},
        {"name": "notContains", "title": "does not contain"},
        {"name": "equals", "title": "equals"},
        {"name": "notEquals", "title": "does not equal"},
        {"name": "set", "title": "is set"},
        {"name": "notSet", "title": "is not set"},
        {"name": "startsWith", "title": "starts with"},
        {"name": "notStartsWith", "title": "does not start with"},
        {"name": "endsWith", "title": "ends with"},
        {"name": "notEndsWith", "title": "does not end with"},
    ],
    "number": [
        {"name": "equals", "title": "equals"},
        {"name": "notEquals", "title": "does not equal"},
        {"name": "set", "title": "is set"},
        {"name": "notSet", "title": "is not set"},
        {"name": "gt", "title": ">"},
        {"name": "gte", "title": ">="},
        {"name": "lt", "title": "<"},
        {"name": "lte", "title": "<="},
    ],
    "time": [
        {"name": "equals", "title": "equals"},
        {"name": "notEquals", "title": "does not equal"},
        {"name": "inDateRange", "title": "in date range"},
        {"name": "notInDateRange", "title": "not in date range"},
        {"name": "afterDate", "title": "after date"},
        {"name": "afterOrOnDate", "title": "after or on date"},
        {"name": "beforeDate", "title": "before date"},
        {"name": "beforeOrOnDate", "title": "before or on date"},
    ],
}


def _member_map(members: Sequence[Mapping[str, Any]]) -> dict:
    return {m["name"]: m for m in members}


class Meta:
    """Wraps a Cube `meta` response with lookups for cubes/members/operators."""

    def __init__(self, meta_response: Mapping[str, Any]):
        self.meta = meta_response
        self.cubes: List[dict] = list(meta_response.get("cubes", []))
        self.cubes_map: Dict[str, dict] = {
            cube["name"]: {
                "measures": _member_map(cube.get("measures", [])),
                "dimensions": _member_map(cube.get("dimensions", [])),
                "segments": _member_map(cube.get("segments", [])),
            }
            for cube in self.cubes
        }

    def members_for_query(self, _query: Any, member_type: str) -> list:
        members = [m for cube in self.cubes for m in cube.get(member_type, [])]
        return sorted(members, key=lambda m: m["title"])

    def members_grouped_by_cube(self) -> Dict[str, List[dict]]:
        grouped: Dict[str, List[dict]] = {"measures": [], "dimensions": [], "segments": [], "timeDimensions": []}

        for cube in self.cubes:
            # `type`/`public` are optional on a cube; JS reads them as `undefined`
            # when absent, so `.get` (-> None) rather than `[...]` (-> KeyError).
            wrapper = {
                "cubeName": cube["name"],
                "cubeTitle": cube["title"],
                "type": cube.get("type"),
                "public": cube.get("public"),
            }
            grouped["measures"].append({**wrapper, "members": cube.get("measures") or []})
            grouped["dimensions"].append({**wrapper, "members": cube.get("dimensions") or []})
            grouped["segments"].append({**wrapper, "members": cube.get("segments") or []})
            grouped["timeDimensions"].append(
                {**wrapper, "members": [d for d in (cube.get("dimensions") or []) if d.get("type") == "time"]}
            )

        return grouped

    def resolve_member(self, member_name: str, member_type: Union[str, Sequence[str]]) -> dict:
        cube_name = member_name.split(".")[0]
        cube = self.cubes_map.get(cube_name)
        if cube is None:
            return {"title": member_name, "error": f"Cube not found {cube_name} for path '{member_name}'"}

        member_types = [member_type] if isinstance(member_type, str) else list(member_type)
        for t in member_types:
            member = cube.get(t, {}).get(member_name)
            if member:
                return member

        return {"title": member_name, "error": f"Path not found '{member_name}'"}

    def default_time_dimension_name_for(self, member_name: str):
        cube_name = member_name.split(".")[0]
        cube = self.cubes_map.get(cube_name)
        if cube is None:
            return None
        for name, dimension in cube.get("dimensions", {}).items():
            if dimension.get("type") == "time":
                return name
        return None

    def filter_operators_for_member(
        self, member_name: str, member_type: Union[str, Sequence[str]]
    ) -> List[dict]:
        member = self.resolve_member(member_name, member_type)
        if "error" in member or "type" not in member or member["type"] == "boolean":
            return _OPERATORS["string"]
        return _OPERATORS.get(member["type"], _OPERATORS["string"])
