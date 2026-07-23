import pytest

from cubejs_client.client.base import run_polling_loop
from cubejs_client.errors import RequestError
from cubejs_client.transport.base import RawResponse


def _no_sleep(_seconds):
    pass


def test_returns_result_on_first_success():
    response = RawResponse(status=200, text='{"data": [1, 2, 3]}')

    result = run_polling_loop(
        request_fn=lambda: response,
        to_result=lambda body: body["data"],
        sleep=_no_sleep,
    )

    assert result == [1, 2, 3]


def test_retries_on_continue_wait_then_succeeds():
    responses = iter(
        [
            RawResponse(status=200, text='{"error": "Continue wait", "stage": "Executing query", "timeElapsed": 100}'),
            RawResponse(status=200, text='{"error": "Continue wait", "stage": "Executing query", "timeElapsed": 200}'),
            RawResponse(status=200, text='{"data": "done"}'),
        ]
    )
    progress_stages = []

    result = run_polling_loop(
        request_fn=lambda: next(responses),
        to_result=lambda body: body["data"],
        progress_callback=lambda p: progress_stages.append(p.stage()),
        sleep=_no_sleep,
    )

    assert result == "done"
    assert len(progress_stages) == 2


def test_raises_request_error_on_non_200_status():
    response = RawResponse(status=403, text='{"error": "Forbidden"}')

    with pytest.raises(RequestError) as exc_info:
        run_polling_loop(request_fn=lambda: response, to_result=lambda body: body, sleep=_no_sleep)

    assert exc_info.value.status == 403
    assert str(exc_info.value) == "Forbidden"


def test_retries_network_error_up_to_budget_then_raises():
    call_count = {"n": 0}

    def request_fn():
        call_count["n"] += 1
        return RawResponse(error="network Error")

    with pytest.raises(RequestError):
        run_polling_loop(
            request_fn=request_fn,
            to_result=lambda body: body,
            network_error_retries=2,
            sleep=_no_sleep,
        )

    # Initial attempt + 2 retries = 3 calls before giving up.
    assert call_count["n"] == 3


def test_recovers_after_transient_network_error_within_budget():
    responses = iter(
        [
            RawResponse(error="network Error"),
            RawResponse(status=200, text='{"data": "ok"}'),
        ]
    )

    result = run_polling_loop(
        request_fn=lambda: next(responses),
        to_result=lambda body: body["data"],
        network_error_retries=2,
        sleep=_no_sleep,
    )

    assert result == "ok"


def test_recovers_after_transient_timeout_within_budget():
    """A timeout is a transport-level failure like a network error and must
    also count against (and be recoverable within) the retry budget."""
    responses = iter(
        [
            RawResponse(error="timeout"),
            RawResponse(status=200, text='{"data": "ok"}'),
        ]
    )

    result = run_polling_loop(
        request_fn=lambda: next(responses),
        to_result=lambda body: body["data"],
        network_error_retries=1,
        sleep=_no_sleep,
    )

    assert result == "ok"
