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

    # 2차: LLM 호출 (행동 생성 + 위기 판정)
    try:
        output = await asyncio.wait_for(
            llm.generate_step(request), timeout=settings.llm_timeout_seconds
        )
    except (asyncio.TimeoutError, LlmTimeoutError) as exc:
        raise timeout() from exc
    except LlmBadResponseError as exc:
        raise bad_response() from exc
    except LlmUnavailableError as exc:
        raise unavailable() from exc

    if output.is_crisis:
        return CRISIS_RESULT

    step = output.step.strip()
    if not step or len(step) > settings.step_max_length:
        raise bad_response()

    return StepResult(is_crisis=False, step=step, can_shrink_more=output.can_shrink_more)
