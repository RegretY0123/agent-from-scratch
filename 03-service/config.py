from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    deepseek_api_key: str

    deepseek_base_url: str = "https://api.deepseek.com"
    request_timeout: float = 30.0

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    max_steps: int = 10
    repeat_limit: int = 2
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 20.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
