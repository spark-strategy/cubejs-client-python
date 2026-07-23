"""Pythonic client for Cube (cube.dev), with pandas integration.

```python
from cubejs_client import cube

client = cube("CUBE-API-TOKEN", api_url="http://localhost:4000/cubejs-api/v1")
result_set = client.load({"measures": ["Orders.count"]})
df = result_set.to_pandas()
```
"""

from __future__ import annotations

from typing import Callable, Optional, Union

from .client.async_client import AsyncCubeClient
from .client.subscription import AsyncSubscription, Subscription
from .client.sync_client import CubeClient
from .core.meta import Meta
from .core.result_set import ResultSet
from .errors import CubeError, CubeSqlError, MutexChangedError, RequestError
from .models.progress import ProgressResult
from .models.sql_query import SqlQuery
from .query.builder import Filter, Member, dim, measure
from .query.model import Query
from .query.pivot_config import PivotConfig
from .query.validate import are_queries_equal, remove_empty_query_fields, validate_query
from .results import pandas_adapter as _pandas_adapter  # noqa: F401  (attaches ResultSet.to_pandas/.df)

__version__ = "0.1.0"


def cube(
    api_token: Optional[Union[str, Callable[[], str]]] = None,
    api_url: Optional[str] = None,
    **kwargs,
) -> CubeClient:
    """Factory mirroring the JS SDK's default export: `cube(apiToken, options)`."""
    if api_url is not None:
        kwargs["api_url"] = api_url
    return CubeClient(api_token, **kwargs)


__all__ = [
    "cube",
    "CubeClient",
    "AsyncCubeClient",
    "Subscription",
    "AsyncSubscription",
    "ResultSet",
    "Meta",
    "SqlQuery",
    "ProgressResult",
    "CubeError",
    "RequestError",
    "CubeSqlError",
    "MutexChangedError",
    "Query",
    "PivotConfig",
    "Filter",
    "Member",
    "dim",
    "measure",
    "validate_query",
    "remove_empty_query_fields",
    "are_queries_equal",
]
