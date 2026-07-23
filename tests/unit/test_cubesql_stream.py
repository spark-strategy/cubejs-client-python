"""Behavioral tests for the CubeSQL streaming chunk parser.

No JS golden fixtures exist for streaming (the JS suite has no requestStream
test), so these are hand-written. They exercise the byte-buffering contract:
lines are reassembled across chunk boundaries, the final unterminated line is
flushed, blank lines are skipped, and a malformed line yields an error chunk
rather than raising.
"""

import json


from cubejs_client.core.cubesql import iter_cubesql_chunks, iter_cubesql_chunks_async

SCHEMA_LINE = json.dumps({"schema": [{"name": "status", "column_type": "String"}], "lastRefreshTime": "T1"})
DATA_LINE = json.dumps({"data": [["Cancelled"], ["Shipped"]]})
ERROR_LINE = json.dumps({"error": "post-processing failed"})


def _chunks(*byte_strs: bytes):
    return list(byte_strs)


def test_classifies_schema_data_error_lines_in_order():
    payload = f"{SCHEMA_LINE}\n{DATA_LINE}\n{ERROR_LINE}\n".encode()

    result = list(iter_cubesql_chunks([payload]))

    assert result == [
        {"type": "schema", "schema": [{"name": "status", "column_type": "String"}], "lastRefreshTime": "T1"},
        {"type": "data", "data": [["Cancelled"], ["Shipped"]]},
        {"type": "error", "error": "post-processing failed"},
    ]


def test_reassembles_a_line_split_across_chunk_boundaries():
    full = f"{SCHEMA_LINE}\n{DATA_LINE}\n".encode()
    # Split mid-way through the schema line so no single chunk holds a whole line.
    split_at = len(SCHEMA_LINE) // 2
    chunks = _chunks(full[:split_at], full[split_at:])

    result = list(iter_cubesql_chunks(chunks))

    assert result == [
        {"type": "schema", "schema": [{"name": "status", "column_type": "String"}], "lastRefreshTime": "T1"},
        {"type": "data", "data": [["Cancelled"], ["Shipped"]]},
    ]


def test_flushes_trailing_line_without_final_newline():
    payload = f"{SCHEMA_LINE}\n{DATA_LINE}".encode()  # no trailing \n

    result = list(iter_cubesql_chunks([payload]))

    assert result[-1] == {"type": "data", "data": [["Cancelled"], ["Shipped"]]}


def test_skips_blank_lines():
    payload = f"{SCHEMA_LINE}\n\n\n{DATA_LINE}\n".encode()

    result = list(iter_cubesql_chunks([payload]))

    assert len(result) == 2


def test_malformed_line_yields_error_chunk_without_raising():
    payload = b'{"data":[["ok"]]}\nnot-json\n'

    result = list(iter_cubesql_chunks([payload]))

    assert result == [
        {"type": "data", "data": [["ok"]]},
        {"type": "error", "error": "Failed to parse JSON line: not-json"},
    ]


def test_empty_array_schema_is_emitted_matching_js_truthiness():
    # JS `if (parsed.schema)` treats an empty array as truthy, so an empty-schema
    # chunk is still emitted — not dropped by Python's list-falsiness.
    payload = b'{"schema":[]}\n'

    result = list(iter_cubesql_chunks([payload]))

    assert result == [{"type": "schema", "schema": []}]


def test_non_object_json_line_is_ignored():
    # A valid-JSON non-object line has no schema/data/error property; JS skips it.
    payload = b'[1, 2, 3]\n42\n"hello"\n'

    result = list(iter_cubesql_chunks([payload]))

    assert result == []


def test_malformed_trailing_line_reports_remaining_json():
    payload = b'{"data":[[1]]}\n{"data":[[2'  # truncated trailing line

    result = list(iter_cubesql_chunks([payload]))

    assert result[0] == {"type": "data", "data": [[1]]}
    assert result[1]["type"] == "error"
    assert "Failed to parse remaining JSON" in result[1]["error"]


def test_reassembles_multibyte_char_split_across_chunk_boundaries():
    # "café" — the 'é' is two UTF-8 bytes (0xC3 0xA9); split them across chunks.
    # ensure_ascii=False keeps 'é' as raw bytes rather than a é escape.
    line = json.dumps({"data": [["café"]]}, ensure_ascii=False).encode("utf-8") + b"\n"
    boundary = line.index(b"\xc3") + 1  # between the two bytes of 'é'
    chunks = _chunks(line[:boundary], line[boundary:])

    result = list(iter_cubesql_chunks(chunks))

    assert result == [{"type": "data", "data": [["café"]]}]


async def test_async_reassembles_multibyte_char_split():
    line = json.dumps({"data": [["café"]]}, ensure_ascii=False).encode("utf-8") + b"\n"
    boundary = line.index(b"\xc3") + 1

    result = [c async for c in iter_cubesql_chunks_async(_aiter([line[:boundary], line[boundary:]]))]

    assert result == [{"type": "data", "data": [["café"]]}]


async def _aiter(chunks):
    for c in chunks:
        yield c


async def test_async_reassembles_and_classifies():
    full = f"{SCHEMA_LINE}\n{DATA_LINE}\n".encode()
    split_at = len(SCHEMA_LINE) // 2

    result = [c async for c in iter_cubesql_chunks_async(_aiter([full[:split_at], full[split_at:]]))]

    assert result == [
        {"type": "schema", "schema": [{"name": "status", "column_type": "String"}], "lastRefreshTime": "T1"},
        {"type": "data", "data": [["Cancelled"], ["Shipped"]]},
    ]
