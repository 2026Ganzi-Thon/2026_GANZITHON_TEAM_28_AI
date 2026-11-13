import asyncio

from app.core.config import get_settings
from app.core.errors import bad_response, timeout, unavailable
from app.llm.base import (
    LlmBadResponseError,
    LlmPort,
    LlmRequest,
    LlmTimeoutError,
    LlmUnavailableError,
    Mode,
)
from app.safety.crisis import has_crisis_keyword
from app.schemas.steps import StepResult

CRISIS_RESULT = StepResult(is_crisis=True, step=None, can_shrink_more=False)


async def generate_step(llm: LlmPort, request: LlmRequest) -> StepResult:
    settings = get_settings()

    # 1차: 자유 입력이 새로 들어오는 FIRST에서만 키워드 검사. 걸리면 LLM을 호출하지 않는다.
    if request.mode == Mode.FIRST and has_crisis_keyword(request.goal):
        return CRISIS_RESULT

    # 2차: LLM 호출 (행동 생성 + 위기 판정). SHRINK에서 이미 나온 행동이 반복되면 한 번 다시 시도한다.
    try:
        output = await _call(llm, request, settings.llm_timeout_seconds)
        if _is_repeat(request, output.step):
            output = await _call(llm, request, settings.llm_timeout_seconds)
    except (asyncio.TimeoutError, LlmTimeoutError) as exc:
        raise timeout() from exc
    except LlmBadResponseError as exc:
        raise bad_response() from exc
    except LlmUnavailableError as exc:
        raise unavailable() from exc

    if output.is_crisis:
        return CRISIS_RESULT

    step = _clean_step(output.step)
    if not step or len(step) > settings.step_max_length or _is_repeat(request, step):
        raise bad_response()

    can_shrink_more = output.can_shrink_more
    if request.mode == Mode.SHRINK and request.shrink_count + 1 >= settings.shrink_max:
        can_shrink_more = False  # 같은 걸음에서 더 작게는 최대 shrink_max번

    reason = output.reason.strip()[: settings.reason_max_length] or None

    return StepResult(
        is_crisis=False,
        step=step,
        can_shrink_more=can_shrink_more,
        reason=reason,
    )


async def check_finish(llm: LlmPort, request: LlmRequest) -> bool:
    """마무리 제안 여부. 보조 기능이라 실패해도 흐름을 막지 않고 false로 둔다."""
    settings = get_settings()
    if request.finish_suggested or request.completed_steps < settings.finish_min_steps:
        return False  # 조건 미달이면 LLM을 부르지 않는다.
    try:
        output = await _call(llm, request, settings.llm_timeout_seconds)
    except (asyncio.TimeoutError, LlmTimeoutError, LlmBadResponseError, LlmUnavailableError):
        return False
    return output.suggest_finish and not output.is_crisis


async def _call(llm: LlmPort, request: LlmRequest, timeout_seconds: float):
    return await asyncio.wait_for(llm.generate_step(request), timeout=timeout_seconds)


def _is_repeat(request: LlmRequest, step: str) -> bool:
    if request.mode != Mode.SHRINK:
        return False
    seen = {_norm(x) for x in request.shrink_history}
    if request.current_step:
        seen.add(_norm(request.current_step))
    return _norm(step) in seen


def _norm(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum())


def _clean_step(text: str) -> str:
    """끝의 마침표·공백을 제거한다. 화면 표기는 "~하기"로 끝나는 구절이다."""
    return text.strip().rstrip(".!。 ").strip()
