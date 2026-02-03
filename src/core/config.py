import os

# src/core/config.py
import os

def _secrets_dict() -> dict:
    """
    Retorna st.secrets como dict, mas NUNCA quebra quando não existe secrets.toml
    (caso comum no ambiente local).
    """
    try:
        import streamlit as st  # import tardio pra não afetar testes
        return dict(st.secrets)  # força avaliação; pode lançar StreamlitSecretNotFoundError
    except Exception:
        return {}

def get_settings() -> dict:
    secrets = _secrets_dict()

    def pick(key: str, default: str = "") -> str:
        # Prioridade: secrets (cloud) -> env var (local/CI) -> default
        return str(secrets.get(key) or os.getenv(key) or default)

    return {
        "ADMIN_EMAIL": pick("ADMIN_EMAIL", "admin@company.com").strip().lower(),
        "ADMIN_PASSWORD": pick("ADMIN_PASSWORD", "Admin@12345"),
        "APP_DB_PATH": pick("APP_DB_PATH", "data/app.db"),
    }

