"""Transport contract, mirroring HttpTransport.ts's `ITransport`/`ITransportResponse`.

Kept intentionally minimal for the sync MVP: a `Transport.request(method, params)`
performs one HTTP call and returns a `RawResponse`. The polling loop
(cubejs_client.client.base.run_polling_loop) calls it repeatedly for retries,
rather than JS's closure/subscribe-based re-invocation — an equivalent
restructuring that avoids needing that callback machinery in Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol


@dataclass
class RawResponse:
    status: Optional[int] = None
    text: Optional[str] = None
    error: Optional[str] = None


class Transport(Protocol):
    authorization: Optional[str]

    def request(self, method: str, params: Mapping[str, Any]) -> RawResponse: ...


class AsyncTransport(Protocol):
    authorization: Optional[str]

    async def request(self, method: str, params: Mapping[str, Any]) -> RawResponse: ...
