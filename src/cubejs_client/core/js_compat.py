"""Small helpers that replicate specific JavaScript runtime semantics.

The JS SDK leans on quirks of `Array.prototype.join`, `Number.parseFloat`,
`Number()`, and ramda's `mergeDeepLeft` / dedup-by-value helpers. Silently
using the "obvious" Python equivalent for any of these produces different
output than the JS client for the same input, so each one is reproduced
explicitly here rather than approximated.
"""

from __future__ import annotations

import math
import re
from typing import Any, Iterable, Mapping

_JS_FLOAT_RE = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?")
_JS_INFINITY_RE = re.compile(r"[+-]?Infinity")


def js_parse_float(value: Any) -> float:
    """Mirror JS `Number.parseFloat`: parse a leading numeric prefix, ignore
    trailing garbage, return NaN if nothing numeric is found."""
    s = str(value).lstrip()
    inf_match = _JS_INFINITY_RE.match(s)
    if inf_match:
        return float("-inf") if s.startswith("-") else float("inf")
    match = _JS_FLOAT_RE.match(s)
    if not match:
        return float("nan")
    try:
        return float(match.group(0))
    except ValueError:
        return float("nan")


def js_number(value: Any) -> Any:
    """Mirror JS `Number(value)` coercion (used for castNumerics).

    Note: does not replicate JS's hex/octal/binary string parsing
    (`Number("0x1A") === 26`) — Python's `float()` can't parse those and this
    returns NaN instead. Cube's numeric columns are not expected to contain
    hex-formatted strings, so this is treated as an acceptable gap for now.
    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip()
    if s == "":
        return 0
    try:
        f = float(s)
    except ValueError:
        return float("nan")
    return int(f) if f.is_integer() and not math.isinf(f) else f


def js_array_join(values: Iterable[Any], sep: str = ",") -> str:
    """Mirror `Array.prototype.join`: None/undefined entries become ''."""
    return sep.join("" if v is None else str(v) for v in values)


def uniq_preserve_order(items: Iterable[Any]) -> list:
    """Mirror ramda's `uniq`: dedupe by value equality, keep first occurrence order."""
    result: list = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def merge_deep_left(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict:
    """Mirror ramda's `mergeDeepLeft(left, right)`: left wins on conflicts,
    recursing when both sides hold a dict for the same key."""
    result = dict(right)
    for key, left_value in left.items():
        right_value = result.get(key)
        if isinstance(left_value, Mapping) and isinstance(right_value, Mapping):
            result[key] = merge_deep_left(left_value, right_value)
        else:
            result[key] = left_value
    return result
