from fastapi import APIRouter, Depends

from app.core.response import api_response
from app.core.security import verify_internal_key
from app.llm.base import LlmPort, LlmRequest, Mode
from app.llm.factory import get_llm
from app.schemas.steps import FirstRequest, NextRequest, ShrinkRequest, StepResult
from app.services.step_service import generate_step

router = APIRouter(prefix="/steps", tags=["steps"], dependencies=[Depends(verify_internal_key)])


def _to_response(result: StepResult) -> dict:
    payload = result.model_dump(by_alias=True)
    if result.is_crisis:
        return api_response(code="CRISIS200", message="도움이 필요할 수 있어요.", result=payload)
    return api_response(result=payload)


@router.post("/first", summary="첫 행동 생성 (위기 확인 포함)")
async def first_step(body: FirstRequest, llm: LlmPort = Depends(get_llm)):
    result = await generate_step(
        llm,
        LlmRequest(
            mode=Mode.FIRST,
            goal=body.goal,
            energy=body.energy,
            burden=body.burden,
            recent_tries=body.recent_tries,
        ),
    )
    return _to_response(result)


@router.post("/shrink", summary="더 작은 행동 생성")
async def shrink_step(body: ShrinkRequest, llm: LlmPort = Depends(get_llm)):
    result = await generate_step(
        llm,
        LlmRequest(
            mode=Mode.SHRINK,
            goal=body.goal,
            energy=body.energy,
            burden=body.burden,
            current_step=body.current_step,
            shrink_history=body.shrink_history,
            shrink_count=body.shrink_count,
            recent_tries=body.recent_tries,
        ),
    )
    return _to_response(result)


@router.post("/next", summary="다음 행동 생성")
async def next_step(body: NextRequest, llm: LlmPort = Depends(get_llm)):
    result = await generate_step(
        llm,
        LlmRequest(
            mode=Mode.NEXT,
            goal=body.goal,
            energy=body.energy,
            burden=body.burden,
            current_step=body.current_step,
            recent_tries=body.recent_tries,
        ),
    )
    return _to_response(result)
