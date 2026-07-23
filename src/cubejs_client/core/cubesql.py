"""Pure parsing of CubeSQL responses (port of the result handlers in
CubeApi.cubeSql / cubeSqlStream, src/index.ts:771-927).

The CubeSQL interface answers in JSON Lines: a schema chunk first, then zero or
more data chunks, with error chunks possible mid-stream. The non-streaming
`cubeSql` endpoint delivers that whole JSONL payload *inside* the response
body's `error` field (a backend quirk — successful results and errors both
arrive as `error`); `parse_cubesql_response` flattens it. The streaming
endpoint delivers the raw JSONL as the HTTP body; `iter_cubesql_chunks` /
`iter_cubesql_chunks_async` yield one typed chunk per line.

Divergence from JS, deliberate: the JS parser special-cases `error === 'timeout'`
/ `'aborted'` sentinels the transport sets on an AbortError. In this port those
transport-level failures are handled upstream by the polling loop (it raises a
`RequestError` before `to_result` ever runs), so they can't reach here; the
branches are omitted rather than kept as dead code.
"""

from __future__ import annotations

import codecs
import json
from typing import AsyncIterable, AsyncIterator, Dict, Iterable, Iterator, List, Optional

from ..errors import CubeSqlError


def parse_cubesql_response(body: dict) -> dict:
    """Flatten a non-streaming CubeSQL body (`{error: "<jsonl>"}`) into
    `{schema, data, lastRefreshTime?}`. Port of index.ts:771-829."""
    if not body or not body.get("error"):
        raise CubeSqlError("Invalid response format")

    payload = body["error"]
    schema_line, *data_lines = payload.split("\n")

    try:
        parsed_schema = json.loads(schema_line)
    except (ValueError, TypeError):
        # Schema line isn't valid JSON — the whole `error` payload is a real error.
        raise CubeSqlError(payload)

    rows: List[list] = []
    for line in data_lines:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except (ValueError, TypeError):
            # A non-JSON line after a valid schema means a malformed payload.
            raise CubeSqlError(payload)
        if not isinstance(parsed, dict):
            # A valid-JSON non-object line (array/number/string) has no `error`
            # or `data` property; JS's `parsed.error`/`parsed.data` are undefined
            # there and it's skipped. Mirror that rather than crashing on `.get`.
            continue
        # An error chunk after the schema (e.g. a post-processing/cast failure)
        # must surface, not be silently dropped as a phantom row.
        if parsed.get("error"):
            raise CubeSqlError(parsed["error"])
        if parsed.get("data") is not None:
            rows.extend(parsed["data"])

    result: Dict[str, object] = {"schema": parsed_schema["schema"], "data": rows}
    if parsed_schema.get("lastRefreshTime"):
        result["lastRefreshTime"] = parsed_schema["lastRefreshTime"]
    return result


def _classify_cubesql_line(line: str) -> Optional[dict]:
    """Map one JSONL line to a typed stream chunk (schema/data/error), or None
    for a blank line. A line that isn't valid JSON yields an error chunk rather
    than raising (matches cubeSqlStream, index.ts:868-895)."""
    if not line.strip():
        return None
    try:
        parsed = json.loads(line)
    except (ValueError, TypeError):
        return {"type": "error", "error": f"Failed to parse JSON line: {line}"}

    if not isinstance(parsed, dict):
        return None

    # JS uses `if (parsed.schema)` / `if (parsed.data)`; an array (even empty) is
    # truthy in JS, so `is not None` — not Python truthiness — is the faithful
    # test for these array-valued keys. `error` is a string, so its emptiness
    # matters (JS truthiness), hence the plain check there.
    if parsed.get("schema") is not None:
        chunk: Dict[str, object] = {"type": "schema", "schema": parsed["schema"]}
        if parsed.get("lastRefreshTime"):
            chunk["lastRefreshTime"] = parsed["lastRefreshTime"]
        return chunk
    if parsed.get("data") is not None:
        return {"type": "data", "data": parsed["data"]}
    if parsed.get("error"):
        return {"type": "error", "error": parsed["error"]}
    return None


def _flush_trailing(buffer: str) -> Optional[dict]:
    """Classify whatever's left after the last newline. A non-empty buffer that
    isn't valid JSON is a 'remaining JSON' error (distinct message from a
    mid-stream bad line, matching cubeSqlStream, index.ts:921-925)."""
    if not buffer.strip():
        return None
    try:
        json.loads(buffer)
    except (ValueError, TypeError):
        return {"type": "error", "error": f"Failed to parse remaining JSON: {buffer}"}
    return _classify_cubesql_line(buffer)


def iter_cubesql_chunks(byte_chunks: Iterable[bytes]) -> Iterator[dict]:
    """Decode a byte stream of CubeSQL JSONL into typed chunks, buffering across
    chunk boundaries so both a JSON line AND a multi-byte UTF-8 character split
    between two byte chunks are reassembled. Port of cubeSqlStream's decode loop
    (index.ts:856-927), whose `TextDecoder({stream:true})` this incremental
    decoder mirrors."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    for raw in byte_chunks:
        buffer += decoder.decode(raw)
        lines = buffer.split("\n")
        buffer = lines.pop()  # trailing partial line (or "" if chunk ended on \n)
        for line in lines:
            chunk = _classify_cubesql_line(line)
            if chunk is not None:
                yield chunk

    buffer += decoder.decode(b"", final=True)  # flush any pending bytes
    trailing = _flush_trailing(buffer)
    if trailing is not None:
        yield trailing


async def iter_cubesql_chunks_async(byte_chunks: AsyncIterable[bytes]) -> AsyncIterator[dict]:
    """Async twin of `iter_cubesql_chunks`, over an async byte iterable."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    async for raw in byte_chunks:
        buffer += decoder.decode(raw)
        lines = buffer.split("\n")
        buffer = lines.pop()
        for line in lines:
            chunk = _classify_cubesql_line(line)
            if chunk is not None:
                yield chunk

    buffer += decoder.decode(b"", final=True)
    trailing = _flush_trailing(buffer)
    if trailing is not None:
        yield trailing
