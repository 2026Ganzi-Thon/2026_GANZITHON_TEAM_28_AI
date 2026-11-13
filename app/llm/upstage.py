import httpx
from pydantic import ValidationError

from app.llm.base import (
    LlmBadResponseError,
    LlmRequest,
    LlmStepOutput,
    LlmTimeoutError,
    LlmUnavailableError,
)
from app.llm.prompt import build_user_prompt, load_system_prompt

# strict 모드: 모든 프로퍼티를 required에 넣고 additionalProperties=false
_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "step_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "is_crisis": {"type": "boolean"},
                "step": {"type": "string"},
                "can_shrink_more": {"type": "boolean"},
                "reason": {"type": "string"},
                "suggest_finish": {"type": "boolean"},
            },
            "required": ["is_crisis", "step", "can_shrink_more", "reason", "suggest_finish"],
            "additionalProperties": False,
        },
    },
}


class UpstageAdapter:
    """Upstage Solar 호출 어댑터 (OpenAI 호환 chat/completions).

    서비스 계층의 asyncio.wait_for와 별개로 httpx 자체 타임아웃도 건다.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            transport=transport,
        )

    async def generate_step(self, request: LlmRequest) -> LlmStepOutput:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": load_system_prompt()},
                {"role": "user", "content": build_user_prompt(request)},
            ],
            "response_format": _RESPONSE_FORMAT,
            "temperature": 0.4,
        }
        try:
            res = await self._client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as exc:
            raise LlmTimeoutError(type(exc).__name__) from exc
        except httpx.HTTPError as exc:  # 네트워크 오류. 원문은 로그에 남기지 않는다.
            raise LlmUnavailableError(type(exc).__name__) from exc

        if res.status_code == 429 or res.status_code >= 500:
            raise LlmUnavailableError(f"HTTP {res.status_code}")
        if res.status_code >= 400:  # 인증·요청 형식 오류도 서비스 입장에서는 사용 불가
            raise LlmUnavailableError(f"HTTP {res.status_code}")

        try:
            choice = res.json()["choices"][0]
            if choice.get("finish_reason") not in (None, "stop"):
                raise LlmBadResponseError(f"finish_reason={choice.get('finish_reason')}")
            return LlmStepOutput.model_validate_json(choice["message"]["content"])
        except LlmBadResponseError:
            raise
        except (ValidationError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise LlmBadResponseError(type(exc).__name__) from exc
