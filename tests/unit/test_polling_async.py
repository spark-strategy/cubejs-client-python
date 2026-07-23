import pytest

from cubejs_client.client.base import run_polling_loop_async
from cubejs_client.errors import RequestError
from cubejs_client.transport.base import RawResponse


async def _no_sleep(_seconds):
    pass


async def test_returns_result_on_first_success():
    response = RawResponse(status=200, text='{"data": [1, 2, 3]}')

    async def request_fn():
        return response

    result = await run_polling_loop_async(
        request_fn=request_fn,
        to_result=lambda body: body["data"],
        sleep=_no_sleep,
    )

    assert result == [1, 2, 3]


async def test_retries_on_continue_wait_then_succeeds():
    responses = iter(
        [
            RawResponse(status=200, text='{"error": "Continue wait", "stage": "Executing query", "timeElapsed": 100}'),
            RawResponse(status=200, text='{"error": "Continue wait", "stage": "Executing query", "timeElapsed": 200}'),
            RawResponse(status=200, text='{"data": "done"}'),
        ]
    )
    progress_stages = []

    async def request_fn():
        return next(responses)

    result = await run_polling_loop_async(
        request_fn=request_fn,
        to_result=lambda body: body["data"],
        progress_callback=lambda p: progress_stages.append(p.stage()),
        sleep=_no_sleep,
    )

    assert result == "done"
    assert len(progress_stages) == 2


async def test_progress_callback_may_be_a_coroutine_function():
    responses = iter(
        [
            RawResponse(status=200, text='{"error": "Continue wait", "stage": "Executing query", "timeElapsed": 100}'),
            RawResponse(status=200, text='{"data": "done"}'),
        ]
    )
    progress_stages = []

    async def request_fn():
        return next(responses)

    async def progress_callback(p):
        progress_stages.append(p.stage())

    result = await run_polling_loop_async(
        request_fn=request_fn,
        to_result=lambda body: body["data"],
        progress_callback=progress_callback,
        sleep=_no_sleep,
    )

    assert result == "done"
    assert progress_stages == ["Executing query"]


async def test_raises_request_error_on_non_200_status():
    response = RawResponse(status=403, text='{"error": "Forbidden"}')

    async def request_fn():
        return response

    with pytest.raises(RequestError) as exc_info:
        await run_polling_loop_async(request_fn=request_fn, to_result=lambda body: body, sleep=_no_sleep)

    assert exc_info.value.status == 403
    assert str(exc_info.value) == "Forbidden"


async def test_retries_network_error_up_to_budget_then_raises():
    call_count = {"n": 0}

    async def request_fn():
        call_count["n"] += 1
        return RawResponse(error="network Error")

    with pytest.raises(RequestError):
        await run_polling_loop_async(
            request_fn=request_fn,
            to_result=lambda body: body,
            network_error_retries=2,
            sleep=_no_sleep,
        )

    assert call_count["n"] == 3


async def test_recovers_after_transient_network_error_within_budget():
    responses = iter(
        [
            RawResponse(error="network Error"),
            RawResponse(status=200, text='{"data": "ok"}'),
        ]
    )

    async def request_fn():
        return next(responses)

    result = await run_polling_loop_async(
        request_fn=request_fn,
        to_result=lambda body: body["data"],
        network_error_retries=2,
        sleep=_no_sleep,
    )

    assert result == "ok"
