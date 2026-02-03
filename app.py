import streamlit as st

from src.core.db import init_db
from src.core.config import get_settings
from src.repos.users_repo import get_user_by_email, create_user
from src.core.ui import sidebar_status, page_header

# ✅ TEM que ser a primeira coisa do Streamlit
st.set_page_config(
    page_title="PlaygroundHub",
    page_icon="🧩",
    layout="wide",
)

# --- Boot ---
init_db()


def ensure_admin():
    s = get_settings()
    email = (s.get("ADMIN_EMAIL") or "").strip().lower()
    pwd = s.get("ADMIN_PASSWORD") or ""
    if email and pwd and not get_user_by_email(email):
        create_user(email=email, password=pwd, role="ADMIN", active=True)


ensure_admin()

# --- Sidebar status (uma vez só) ---
sidebar_status()

# --- Menu superior: breadcrumb (PlaygroundHub > Início) + título ---
page_header("Início", title="PlaygroundHub", subtitle="Playground corporativo com controle, papéis e auditoria.")
st.write("Use o menu lateral para navegar.")
