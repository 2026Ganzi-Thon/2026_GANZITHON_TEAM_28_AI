"""위기 1차 키워드 검사.

주의: 아래 목록은 시작용 초안이다. 확정 전에 직접 표현, 돌려 말하는 표현,
오탐 사례("죽을 만큼 피곤해" 등)로 만든 테스트 세트로 보강하고 검토해야 한다.
오탐보다 미탐이 더 위험하므로 애매한 경우는 2차(LLM) 판정에서 한 번 더 본다.
"""

import re

_KEYWORDS = [
    "죽고싶",
    "죽을까",
    "죽어버리",
    "죽는게나",
    "죽는게낫",
    "자살",
    "자해",
    "목숨을끊",
    "스스로목숨",
    "사라지고싶",
    "사라져버리고싶",
    "살기싫",
    "살고싶지않",
    "살아갈이유",
    "생을마감",
    "극단적인선택",
    "손목을긋",
    "뛰어내리고싶",
]

_NOISE = re.compile(r"[\s\.\,\!\?\~\-_​]+")


def _normalize(text: str) -> str:
    return _NOISE.sub("", text)


def has_crisis_keyword(text: str) -> bool:
    normalized = _normalize(text)
    return any(keyword in normalized for keyword in _KEYWORDS)
