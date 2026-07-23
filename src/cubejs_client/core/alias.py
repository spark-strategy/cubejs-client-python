"""Port of aliasSeries (src/utils.ts:385-395)."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Set


def alias_series(
    values: Sequence[Any],
    index: int,
    pivot_config: Optional[Mapping[str, Any]] = None,
    duplicate_measures: Optional[Set[Any]] = None,
) -> list:
    duplicate_measures = duplicate_measures or set()
    non_null_values = [v for v in values if v is not None]

    if pivot_config:
        alias_series_list = pivot_config.get("aliasSeries")
        if alias_series_list and index < len(alias_series_list) and alias_series_list[index]:
            return [alias_series_list[index], *non_null_values]

    first = non_null_values[0] if non_null_values else None
    if first in duplicate_measures:
        return [index, *non_null_values]

    return non_null_values
