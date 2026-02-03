from pathlib import Path
import streamlit as st

from src.core.db import init_db
from src.core.config import get_settings
from src.repos.users_repo import get_user_by_email, create_user
from src.core.ui import sidebar_status

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

# --- Header (logo pequena + nome ao lado) ---
logo_path = Path("assets/logo.png")
col1, col2 = st.columns([1, 8], vertical_alignment="center")

with col1:
    if logo_path.exists():
        st.image(str(logo_path), width=56)

with col2:
    st.markdown("## PlaygroundHub")
    st.caption("Playground corporativo com controle, papéis e auditoria.")

st.divider()
st.write("Use o menu lateral para navegar.")
