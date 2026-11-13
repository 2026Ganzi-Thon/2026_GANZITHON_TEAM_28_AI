from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_internal_key: str = ""
    llm_provider: str = "mock"  # mock | gemini | upstage
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    upstage_api_key: str = ""
    upstage_model: str = "solar-pro4"
    upstage_base_url: str = "https://api.upstage.ai/v1"
    llm_timeout_seconds: float = 6.0  # 백엔드 읽기 7초 + 1회 재시도가 프론트 15초 안에 끝나도록
    step_max_length: int = 60
    shrink_max: int = 5  # API 명세서(11/12 확정): 같은 걸음에서 더 작게 최대 5번. Figma #4 는 3번이라 팀 확인 중
    reason_max_length: int = 80
    finish_min_steps: int = 3  # Figma 확정 #5: 3걸음 이상 내디딘 뒤 마무리 제안


@lru_cache
def get_settings() -> Settings:
    return Settings()
