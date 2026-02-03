from typing import Optional

from openai import OpenAI

from src.core.config import get_settings


_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        api_key = (settings.get('OPENAI_API_KEY') or '').strip()
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY nao configurada.')
        _client = OpenAI(api_key=api_key)
    return _client
