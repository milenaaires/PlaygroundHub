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
page_header("Home", title="PlaygroundHub", subtitle="Playground corporativo com controle, papéis e auditoria.")

st.markdown("Use o menu lateral para navegar.")

st.markdown("---")
st.markdown("### Visão geral")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🔐 Login** — Autenticação por e-mail e senha. Acesso conforme perfil (Admin ou User).")
    st.markdown("**👤 Área do usuário** — Criar e editar agentes de IA (modelo, prompt, tipo Chat/SQL), testar no chat e manter histórico de conversas por agente. Anexar PDFs nas conversas.")
    st.markdown("**📋 Compliance** — Auditoria dos prompts enviados pelos usuários.")
with col2:
    st.markdown("**⚙️ Admin** — Gerenciar usuários (listar, editar, ativar/desativar, redefinir senha).")
    st.markdown("**🧩 Agentes** — Cada agente tem nome, descrição, modelo (ex.: GPT-4o), tokens, temperatura, system prompt e opção de conexão SQL. Chats são salvos e reabríveis.")

st.markdown("---")
st.caption("PlaygroundHub — controle de acesso, agentes configuráveis e auditoria.")
