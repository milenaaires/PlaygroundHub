import streamlit as st

ROLE_ADMIN = "ADMIN"
ROLE_USER = "USER"
ROLE_COMPLIANCE = "COMPLIANCE"

def is_allowed(role: str | None, allowed_roles: set[str]) -> bool:
    return role in allowed_roles

def require_auth():
    if not st.session_state.get("authenticated"):
        st.error("Você precisa fazer login para acessar esta página.")
        st.stop()

def require_roles(allowed_roles: set[str]):
    require_auth()
    role = st.session_state.get("role")
    if not is_allowed(role, allowed_roles):
        st.error("Acesso negado para o seu perfil.")
        st.stop()
