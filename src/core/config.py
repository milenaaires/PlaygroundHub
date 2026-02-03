import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(ROOT / '.env')
except Exception:
    pass

# src/core/config.py

def _secrets_dict() -> dict:
    '''
    Retorna st.secrets como dict, mas NUNCA quebra quando nao existe secrets.toml
    (caso comum no ambiente local).
    '''
    try:
        import streamlit as st  # import tardio pra nao afetar testes
        return dict(st.secrets)  # forca avaliacao; pode lancar StreamlitSecretNotFoundError
    except Exception:
        return {}


def get_settings() -> dict:
    secrets = _secrets_dict()

    def pick(key: str, default: str = '') -> str:
        # Prioridade: secrets (cloud) -> env var (local/CI) -> default
        return str(secrets.get(key) or os.getenv(key) or default)

    max_tokens = pick('OPENAI_MAX_OUTPUT_TOKENS', '')
    if not max_tokens:
        max_tokens = pick('OPENAI_MAX_TOKENS', '1024')

    return {
        'ADMIN_EMAIL': pick('ADMIN_EMAIL', 'admin@company.com').strip().lower(),
        'ADMIN_PASSWORD': pick('ADMIN_PASSWORD', 'Admin@12345'),
        'APP_DB_PATH': pick('APP_DB_PATH', 'data/app.db'),
        'OPENAI_API_KEY': pick('OPENAI_API_KEY', '').strip(),
        'OPENAI_MODEL': pick('OPENAI_MODEL', 'gpt-4o-mini').strip(),
        'OPENAI_TEMPERATURE': pick('OPENAI_TEMPERATURE', '0.7').strip(),
        'OPENAI_MAX_OUTPUT_TOKENS': max_tokens.strip(),
    }
