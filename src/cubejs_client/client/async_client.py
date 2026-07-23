"""Port of CubeApi (async half): load/meta/sql/dry_run/cube_sql. Kept in lockstep
with sync_client.py by hand — same params/baseRequestId/decode wiring, `await`ed
throughout.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncIterator, Callable, List, Optional, Union

from ..core.cubesql import iter_cubesql_chunks_async, parse_cubesql_response
from ..core.meta import Meta
from ..core.response_decode import decode_response_data
from ..core.result_set import ResultSet
from ..errors import RequestError
from ..models.progress import ProgressResult
from ..models.sql_query import SqlQuery
from ..query.model import QueryLike, patch_query_response_format, to_query_dict
from ..transport.base import AsyncTransport
from ..transport.http_async import AsyncHttpTransport
from .base import run_polling_loop_async, run_subscribe_loop_async
from .subscription import AsyncSubscription


class AsyncCubeClient:
    """Asynchronous Cube API client.

    ```python
    from cubejs_client import AsyncCubeClient

    client = AsyncCubeClient(api_url="http://localhost:4000/cubejs-api/v1", api_token="TOKEN")
    result_set = await client.load({"measures": ["Orders.count"]})
    df = result_set.to_pandas()
    ```
    """

    def __init__(
        self,
        api_token: Optional[Union[str, Callable[[], str]]] = None,
        *,
        api_url: Optional[str] = None,
        transport: Optional[AsyncTransport] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = None,
        credentials: Optional[str] = None,
        fetch_timeout: Optional[float] = None,
        poll_interval: float = 5.0,
        cast_numerics: bool = False,
        parse_date_measures: bool = False,
        network_error_retries: int = 0,
    ):
        if transport is None and not api_url:
            raise ValueError("The `api_url` option is required")

        self._api_token = api_token
        self._transport: AsyncTransport = transport or AsyncHttpTransport(
            api_url=api_url,  # type: ignore[arg-type]
            authorization=api_token if isinstance(api_token, str) else None,
            method=method,
            headers=headers,
            credentials=credentials,
            fetch_timeout=fetch_timeout,
        )
        self._poll_interval = poll_interval
        self._cast_numerics = cast_numerics
        self._parse_date_measures = parse_date_measures
        self._network_error_retries = network_error_retries

    def _update_authorization(self) -> None:
        if callable(self._api_token):
            token = self._api_token()
            if self._transport.authorization != token:
                self._transport.authorization = token

    async def _load_method(
        self,
        request_fn: Callable[[], Any],
        to_result: Callable[[dict], Any],
        *,
        progress_callback: Optional[Callable[[ProgressResult], None]] = None,
    ) -> Any:
        self._update_authorization()
        return await run_polling_loop_async(
            request_fn=request_fn,
            to_result=to_result,
            poll_interval=self._poll_interval,
            network_error_retries=self._network_error_retries,
            progress_callback=progress_callback,
        )

    async def load(
        self,
        query: QueryLike,
        *,
        cast_numerics: Optional[bool] = None,
        parse_date_measures: Optional[bool] = None,
        cache: Optional[str] = None,
        response_format: str = "default",
        progress_callback: Optional[Callable[[ProgressResult], None]] = None,
    ) -> ResultSet:
        query_dict = patch_query_response_format(to_query_dict(query), response_format)
        params = {
            "query": query_dict,
            "queryType": "multi",
            "baseRequestId": str(uuid.uuid4()),
        }
        if cache:
            params["cache"] = cache

        effective_cast_numerics = self._cast_numerics if cast_numerics is None else cast_numerics
        effective_parse_dates = self._parse_date_measures if parse_date_measures is None else parse_date_measures

        def to_result(body: dict) -> ResultSet:
            decode_response_data(body, cast_numerics=effective_cast_numerics)
            return ResultSet(body, {"parseDateMeasures": effective_parse_dates})

        return await self._load_method(
            lambda: self._transport.request("load", params), to_result, progress_callback=progress_callback
        )

    async def sql(self, query: QueryLike) -> Union[SqlQuery, List[SqlQuery]]:
        params = {"query": to_query_dict(query), "baseRequestId": str(uuid.uuid4())}

        def to_result(body: Any) -> Union[SqlQuery, List[SqlQuery]]:
            if isinstance(body, list):
                return [SqlQuery(b) for b in body]
            return SqlQuery(body)

        return await self._load_method(lambda: self._transport.request("sql", params), to_result)

    async def meta(self) -> Meta:
        params = {"baseRequestId": str(uuid.uuid4())}
        return await self._load_method(lambda: self._transport.request("meta", params), lambda body: Meta(body))

    async def dry_run(self, query: QueryLike) -> dict:
        params = {"query": to_query_dict(query), "baseRequestId": str(uuid.uuid4())}
        return await self._load_method(lambda: self._transport.request("dry-run", params), lambda body: body)

    async def cube_sql(self, sql_query: str, *, timeout: Optional[float] = None, cache: Optional[str] = None) -> dict:
        """Async twin of ``CubeClient.cube_sql`` — see there for semantics."""
        params: dict = {
            "query": sql_query,
            "method": "POST",
            "fetchTimeout": timeout,
            "baseRequestId": str(uuid.uuid4()),
            "throwContinueWait": True,
        }
        if cache:
            params["cache"] = cache
        return await self._load_method(lambda: self._transport.request("cubesql", params), parse_cubesql_response)

    async def cube_sql_stream(
        self, sql_query: str, *, timeout: Optional[float] = None, cache: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """Async twin of ``CubeClient.cube_sql_stream`` — see there for semantics."""
        request_stream = getattr(self._transport, "request_stream", None)
        if request_stream is None:
            raise RuntimeError("Transport does not support streaming")
        self._update_authorization()
        byte_chunks = request_stream(
            "cubesql",
            params={"query": sql_query, "cache": cache},
            http_method="POST",
            fetch_timeout=timeout,
            base_request_id=str(uuid.uuid4()),
        )
        async for chunk in iter_cubesql_chunks_async(byte_chunks):
            yield chunk

    def subscribe(
        self,
        query: QueryLike,
        callback: Callable[[Optional[RequestError], Optional[ResultSet]], Any],
        *,
        cast_numerics: Optional[bool] = None,
        parse_date_measures: Optional[bool] = None,
        cache: Optional[str] = None,
    ) -> AsyncSubscription:
        """Async twin of ``CubeClient.subscribe`` — runs the poll loop as an
        ``asyncio.Task`` (cancelled by ``await subscription.unsubscribe()``).
        The callback may be sync or async. Not a coroutine: it schedules the task
        and returns immediately, so call it without ``await``."""
        params: dict = {
            "query": to_query_dict(query),
            "queryType": "multi",
            "baseRequestId": str(uuid.uuid4()),
        }
        if cache:
            params["cache"] = cache

        effective_cast_numerics = self._cast_numerics if cast_numerics is None else cast_numerics
        effective_parse_dates = self._parse_date_measures if parse_date_measures is None else parse_date_measures

        def to_result(body: dict) -> ResultSet:
            decode_response_data(body, cast_numerics=effective_cast_numerics)
            return ResultSet(body, {"parseDateMeasures": effective_parse_dates})

        stop_event = asyncio.Event()

        async def _run() -> None:
            try:
                await run_subscribe_loop_async(
                    request_fn=lambda: self._transport.request("subscribe", params),
                    to_result=to_result,
                    callback=callback,
                    should_stop=stop_event.is_set,
                    poll_interval=self._poll_interval,
                    network_error_retries=self._network_error_retries,
                    update_authorization=self._update_authorization,
                )
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # noqa: BLE001 - surfaced via AsyncSubscription.unsubscribe()
                subscription.exception = exc

        task = asyncio.create_task(_run())
        subscription = AsyncSubscription(task, stop_event)
        return subscription
