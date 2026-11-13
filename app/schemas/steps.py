from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Level = Annotated[int, Field(ge=1, le=4)]  # 백엔드/Figma: 에너지·부담 모두 4단계


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StepBase(CamelModel):
    goal: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]  # 50자 제한은 백엔드가 검증(Figma #7)
    # energy 1=완전히 방전됨~4=꽤 괜찮아요, burden 1=너무 막막해요~4=해볼 만해요 (순서는 Figma 라벨 기준, 백엔드 확인 필요)
    energy: Level
    burden: Level
    recent_tries: list[ShortText] = Field(default_factory=list, max_length=10)


class FirstRequest(StepBase):
    pass


class ShrinkRequest(StepBase):
    current_step: ShortText
    shrink_history: list[ShortText] = Field(max_length=5)
    shrink_count: int = Field(ge=0, le=5)
    is_last_step: bool = False  # 줄이는 대상 행동이 마지막 걸음이면 true. 결과에 그대로 이어진다.


class NextRequest(StepBase):
    current_step: ShortText
    # "해봤어요" 뒤 다시 고른 에너지: 그대로예요=SAME, 조금 생겼어요=UP, 더 지쳤어요=DOWN
    energy_change: Literal["SAME", "UP", "DOWN"] | None = None
    # 지금까지 해본(해봤어요) 걸음 수와, 이미 마무리 제안(isLastStep)을 한 목표인지. 마지막 걸음 판단용
    completed_steps: int = Field(default=0, ge=0, le=1000)
    finish_suggested: bool = False


class StepResult(CamelModel):
    is_crisis: bool
    step: str | None
    can_shrink_more: bool
    reason: str | None = None  # 화면의 이유 문구(AI 출력 여부는 팀 확인 필요)
    is_last_step: bool = False  # 이 걸음이 목표의 마지막 걸음이면 true (해봤어요 후 마무리 제안)
