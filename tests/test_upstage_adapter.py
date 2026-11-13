import asyncio
import json

import httpx
import pytest

from app.llm.base import (
    LlmBadResponseError,
    LlmRequest,
    LlmTimeoutError,
    LlmUnavailableError,
    Mode,
)
from app.llm.upstage import UpstageAdapter

REQ = LlmRequest(mode=Mode.FIRST, goal="과제 완료하기", energy=2, burden=4)


def make(handler):
    return UpstageAdapter(
        "k", "solar-pro4", "https://api.upstage.ai/v1", 5, httpx.MockTransport(handler)
    )


def ok(content, finish="stop"):
    return httpx.Response(
        200, json={"choices": [{"finish_reason": finish, "message": {"content": content}}]}
    )


def run(adapter):
    return asyncio.run(adapter.generate_step(REQ))


def test_success_and_request_shape():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["Authorization"]
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return ok('{"is_crisis": false, "step": "노트북 켜기", "can_shrink_more": true}')

    out = run(make(handler))
    assert out.step == "노트북 켜기"
    assert seen["auth"] == "Bearer k"
    assert seen["url"] == "https://api.upstage.ai/v1/chat/completions"
    assert seen["body"]["model"] == "solar-pro4"
    assert seen["body"]["response_format"]["json_schema"]["strict"] is True


@pytest.mark.parametrize("status", [401, 429, 500])
def test_http_errors_are_unavailable(status):
    with pytest.raises(LlmUnavailableError):
        run(make(lambda r: httpx.Response(status, json={})))


def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(LlmTimeoutError):
        run(make(handler))


def test_network_error_is_unavailable():
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(LlmUnavailableError):
        run(make(handler))


@pytest.mark.parametrize("content", ["not json", '{"step": 1}', ""])
def test_bad_json_is_bad_response(content):
    with pytest.raises(LlmBadResponseError):
        run(make(lambda r: ok(content)))


def test_truncated_is_bad_response():
    body = '{"is_crisis": false, "step": "a", "can_shrink_more": true}'
    with pytest.raises(LlmBadResponseError):
        run(make(lambda r: ok(body, finish="length")))


def test_unexpected_body_is_bad_response():
    with pytest.raises(LlmBadResponseError):
        run(make(lambda r: httpx.Response(200, json={"oops": 1})))
