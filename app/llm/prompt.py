from functools import lru_cache
from pathlib import Path

from app.llm.base import LlmRequest

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache
def load_system_prompt() -> str:
    return (_PROMPT_DIR / "step_system.txt").read_text(encoding="utf-8")


def build_user_prompt(req: LlmRequest) -> str:
    """사용자 입력은 태그로 감싸 데이터로 구분한다."""
    lines = [
        f"mode: {req.mode.value}",
        f"<goal>{req.goal}</goal>",
        # 방향은 미결정: 현재 가정은 에너지 1=매우 낮음~5=높음, 부담 1=적음~5=매우 큼
        f"에너지(1 낮음~5 높음): {req.energy}",
        f"부담(1 적음~5 매우 큼): {req.burden}",
    ]
    if req.current_step:
        lines.append(f"<current_step>{req.current_step}</current_step>")
    if req.shrink_history:
        joined = " / ".join(req.shrink_history)
        lines.append(f"<shrink_history>{joined}</shrink_history>")
        lines.append(f"줄인 횟수: {req.shrink_count}")
    if req.recent_tries:
        joined = " / ".join(req.recent_tries)
        lines.append(f"<recent_tries>{joined}</recent_tries>")
    return "\n".join(lines)
