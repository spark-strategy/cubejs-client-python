"""Port of CubeApi.loadResponseInternal's data-shaping logic (src/index.ts:486-549).

Mutates a `LoadResponse`-shaped dict in place: applies `castNumerics`, then
unpacks `compact`/`columnar` response formats into plain row dicts so the
rest of the pipeline (ResultSet) only ever sees the default row-dict shape.
"""

from __future__ import annotations

from typing import Any, MutableMapping

from .js_compat import js_number


def decode_response_data(response: MutableMapping[str, Any], cast_numerics: bool = False) -> None:
    # NOTE: matching src/index.ts:486-513, the castNumerics loop runs BEFORE
    # the compact/columnar unpacking below, so it assumes `result["data"]` is
    # already a list of row dicts. Combining `cast_numerics=True` with a
    # `compact`/`columnar` responseFormat crashes here (data is still
    # `{"members": [...], "dataset"/"columns": [...]}` at this point) — this
    # is a faithfully-reproduced ordering bug in the JS SDK itself, not a
    # Python-specific regression, and is not "fixed" here to stay in sync
    # with upstream behavior.
    results = response.get("results") or []
    if not results:
        return

    if cast_numerics:
        for result in results:
            annotation = result["annotation"]
            numeric_members = [
                key
                for key, meta in {**annotation.get("measures", {}), **annotation.get("dimensions", {})}.items()
                if meta.get("type") == "number"
            ]
            for row in result["data"]:
                for key in numeric_members:
                    if row.get(key) is not None:
                        row[key] = js_number(row[key])

    response_format = results[0]["query"].get("responseFormat")

    if response_format == "compact":
        for result in results:
            members = result["data"]["members"]
            dataset = result["data"]["dataset"]
            result["data"] = [dict(zip(members, row)) for row in dataset]
    elif response_format == "columnar":
        for result in results:
            members = result["data"]["members"]
            columns = result["data"]["columns"]
            row_count = len(columns[0]) if columns else 0
            result["data"] = [
                {member: columns[k][i] for k, member in enumerate(members)} for i in range(row_count)
            ]
