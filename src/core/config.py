import os

def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)

DB_PATH = os.getenv("APP_DB_PATH", "data/app.db")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
