from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Level = Annotated[int, Field(ge=1, le=5)]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StepBase(CamelModel):
    goal: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    # 방향은 미결정: 현재 가정은 energy 1=매우 낮음~5=높음, burden 1=부담 적음~5=매우 큼
    energy: Level
    burden: Level
    recent_tries: list[ShortText] = Field(default_factory=list, max_length=10)


class FirstRequest(StepBase):
    pass


class ShrinkRequest(StepBase):
    current_step: ShortText
    shrink_history: list[ShortText] = Field(max_length=5)
    shrink_count: int = Field(ge=0, le=5)


class NextRequest(StepBase):
    current_step: ShortText


class StepResult(CamelModel):
    is_crisis: bool
    step: str | None
    can_shrink_more: bool
