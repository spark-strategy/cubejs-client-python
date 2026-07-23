"""Port of SqlQuery.ts."""

from __future__ import annotations

from typing import Any, Mapping


class SqlQuery:
    def __init__(self, sql_query_wrapper: Mapping[str, Any]):
        self._sql_query = sql_query_wrapper

    def raw_query(self) -> dict:
        return self._sql_query["sql"]

    def sql(self) -> str:
        return self.raw_query()["sql"][0]
