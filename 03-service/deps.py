from functools import lru_cache

from config import get_settings
from openai import OpenAI


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.request_timeout,
        max_retries=0,
    )
