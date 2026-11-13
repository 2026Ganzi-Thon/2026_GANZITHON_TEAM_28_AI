from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LlmPort
from app.llm.mock import MockAdapter


@lru_cache
def get_llm() -> LlmPort:
    settings = get_settings()
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("LLM_PROVIDER=gemini 이면 GEMINI_API_KEY가 필요합니다.")
        from app.llm.gemini import GeminiAdapter

        return GeminiAdapter(settings.gemini_api_key, settings.gemini_model)
    return MockAdapter()
