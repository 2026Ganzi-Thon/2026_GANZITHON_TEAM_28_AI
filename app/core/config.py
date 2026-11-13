from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_internal_key: str = ""
    llm_provider: str = "mock"  # mock | gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: float = 10.0
    step_max_length: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
