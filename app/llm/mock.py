from app.llm.base import LlmRequest, LlmStepOutput, Mode

_LADDER = [
    "과제 자료 확인하기",
    "노트북 켜기",
    "책상에 앉기",
    "노트북 앞에 서 있기",
    "의자에 손만 올려 보기",
]
_NEXT = "자료 첫 줄만 읽어 보기"


class MockAdapter:
    """키 없이 API 흐름을 개발·테스트하기 위한 가짜 LLM. 위기 2차 판정은 항상 false."""

    async def generate_step(self, request: LlmRequest) -> LlmStepOutput:
        if request.mode == Mode.SHRINK:
            level = min(request.shrink_count + 1, len(_LADDER) - 1)
            return LlmStepOutput(
                step=_LADDER[level],
                can_shrink_more=request.shrink_count + 1 < 3,
                reason="더 작게 나눠봤어요",
            )
        if request.mode == Mode.NEXT:
            return LlmStepOutput(
                step=_NEXT,
                can_shrink_more=True,
                reason="지금 에너지에 맞춰 골랐어요",
                suggest_finish=request.completed_steps >= 3 and not request.finish_suggested,
            )
        return LlmStepOutput(
            step=_LADDER[0], can_shrink_more=True, reason="지금 에너지에 맞춰 가장 작은 걸음을 골랐어요"
        )
