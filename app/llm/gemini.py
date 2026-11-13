from pydantic import ValidationError

from app.llm.base import (
    LlmBadResponseError,
    LlmRequest,
    LlmStepOutput,
    LlmUnavailableError,
)
from app.llm.prompt import build_user_prompt, load_system_prompt


class GeminiAdapter:
    """Gemini 호출 어댑터. 타임아웃은 서비스 계층에서 asyncio.wait_for로 건다."""

    def __init__(self, api_key: str, model: str):
        from google import genai  # 키 없이 mock만 쓸 때는 import하지 않는다

        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_step(self, request: LlmRequest) -> LlmStepOutput:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=load_system_prompt(),
            response_mime_type="application/json",
            response_schema=LlmStepOutput,
            temperature=0.4,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=build_user_prompt(request),
                config=config,
            )
        except Exception as exc:  # 한도 초과, 네트워크 오류 등. 원문은 로그에 남기지 않는다.
            raise LlmUnavailableError(type(exc).__name__) from exc

        try:
            return LlmStepOutput.model_validate_json(response.text)
        except (ValidationError, ValueError, TypeError) as exc:
            raise LlmBadResponseError(type(exc).__name__) from exc
