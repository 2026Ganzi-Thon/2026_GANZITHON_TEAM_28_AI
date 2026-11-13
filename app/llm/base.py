from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from pydantic import BaseModel


class Mode(str, Enum):
    FIRST = "FIRST"
    SHRINK = "SHRINK"
    NEXT = "NEXT"


@dataclass
class LlmRequest:
    mode: Mode
    goal: str
    energy: int
    burden: int
    current_step: str | None = None
    shrink_history: list[str] = field(default_factory=list)
    shrink_count: int = 0
    recent_tries: list[str] = field(default_factory=list)
    energy_change: str | None = None
    completed_steps: int = 0
    finish_suggested: bool = False


class LlmStepOutput(BaseModel):
    """LLM이 반환해야 하는 JSON 구조. 위기이면 step은 빈 문자열."""

    is_crisis: bool = False
    step: str = ""
    can_shrink_more: bool = True
    reason: str = ""
    suggest_finish: bool = False


class LlmTimeoutError(Exception):
    pass


class LlmUnavailableError(Exception):
    pass


class LlmBadResponseError(Exception):
    pass


class LlmPort(Protocol):
    async def generate_step(self, request: LlmRequest) -> LlmStepOutput: ...
