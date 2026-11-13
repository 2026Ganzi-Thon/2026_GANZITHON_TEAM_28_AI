from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Level = Annotated[int, Field(ge=1, le=5)]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StepBase(CamelModel):
    goal: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    # 방향은 미결정: 현재 가정은 energy 1=매우 낮음~5=높음, burden 1=부담 적음~5=매우 큼
    energy: Level
    burden: Level
    recent_tries: list[ShortText] = Field(default_factory=list, max_length=10)


class FirstRequest(StepBase):
    pass


class ShrinkRequest(StepBase):
    current_step: ShortText
    shrink_history: list[ShortText] = Field(max_length=3)
    shrink_count: int = Field(ge=0, le=3)


class NextRequest(StepBase):
    current_step: ShortText
    # "해봤어요" 뒤 다시 고른 에너지: 그대로예요=SAME, 조금 생겼어요=UP, 더 지쳤어요=DOWN
    energy_change: Literal["SAME", "UP", "DOWN"] | None = None
    # 지금까지 내디딘(해봤어요) 걸음 수. AI 마무리 제안 판단용
    completed_steps: int = Field(default=0, ge=0, le=1000)
    # 이미 마무리 제안을 한 목표인지(목표당 1번)
    finish_suggested: bool = False


class StepResult(CamelModel):
    is_crisis: bool
    step: str | None
    can_shrink_more: bool
    reason: str | None = None  # 화면의 이유 문구(AI 출력 여부는 팀 확인 필요)
    suggest_finish: bool = False  # next에서만 true 가능
