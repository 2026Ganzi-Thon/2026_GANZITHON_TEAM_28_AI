from functools import lru_cache
from pathlib import Path

from app.llm.base import LlmRequest

# 순서는 Figma 라벨 기준(백엔드 확인 필요). 숫자 대신 라벨을 넘겨 모델이 방향을 헷갈리지 않게 한다.
_ENERGY = {1: "완전히 방전됨", 2: "조금 남아 있음", 3: "보통이에요", 4: "꽤 괜찮아요"}
_BURDEN = {1: "너무 막막해요", 2: "꽤 부담돼요", 3: "약간 부담돼요", 4: "해볼 만해요"}

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache
def load_system_prompt() -> str:
    return (_PROMPT_DIR / "step_system.txt").read_text(encoding="utf-8")


def build_user_prompt(req: LlmRequest) -> str:
    """사용자 입력은 태그로 감싸 데이터로 구분한다."""
    lines = [
        f"mode: {req.mode.value}",
        f"<goal>{req.goal}</goal>",
        f"에너지: {_ENERGY.get(req.energy, req.energy)}",
        f"부담: {_BURDEN.get(req.burden, req.burden)}",
    ]
    if req.energy_change:
        label = {"SAME": "그대로예요", "UP": "조금 생겼어요", "DOWN": "더 지쳤어요"}.get(req.energy_change)
        if label:
            lines.append(f"방금 걸음 뒤 다시 고른 에너지: {label}")
    if req.mode.value == "NEXT":
        lines.append(f"지금까지 해본 걸음 수: {req.completed_steps}")
        lines.append(f"이미 마무리 제안한 목표인가: {'예' if req.finish_suggested else '아니오'}")
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
