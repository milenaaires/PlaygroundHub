import streamlit as st

from src.auth.rbac import require_roles, ROLE_ADMIN
from src.core.ui import page_header
from src.repos.users_repo import list_users, create_user, update_user, set_password
from src.core.ui import sidebar_status

sidebar_status()

require_roles([ROLE_ADMIN])

page_header("Admin — Usuários", subtitle="Gerencie usuários e papéis.")

# ---------- Helpers ----------
def _email_ok(email: str) -> bool:
    e = (email or "").strip().lower()
    return ("@" in e) and ("." in e)

def _pw_ok(pw: str) -> bool:
    return pw is not None and len(pw) >= 8


# ---------- Dialogs (pop-ups) ----------
@st.dialog("➕ Criar usuário")
def dialog_create_user():
    with st.form("form_create_user", clear_on_submit=True):
        email = (st.text_input("E-mail (novo usuário)", placeholder="user@empresa.com") or "").strip().lower()
        role = st.selectbox("Role", ["ADMIN", "USER"])
        active = st.checkbox("Ativo", value=True)
        pw1 = st.text_input("Senha inicial", type="password")
        pw2 = st.text_input("Confirmar senha", type="password")
        ok = st.form_submit_button("Criar", type="primary")

    if ok:
        if not _email_ok(email):
            st.error("E-mail inválido.")
            return
        if not _pw_ok(pw1):
            st.error("Senha deve ter pelo menos 8 caracteres.")
            return
        if pw1 != pw2:
            st.error("As senhas não conferem.")
            return

        create_user(email=email, password=pw1, role=role, active=active)
        st.success("Usuário criado com sucesso.")
        st.rerun()


@st.dialog("✏️ Editar usuário")
def dialog_edit_user():
    users = list_users()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    # escolha por id, mas mostrando email
    options = {f'{u["id"]} — {u["email"]}': u for u in users}
    pick = st.selectbox("Selecione o usuário", list(options.keys()))
    u = options[pick]

    me_id = st.session_state.get("user_id")

    with st.form("form_edit_user"):
        st.text_input("E-mail", value=u["email"], disabled=True)
        role = st.selectbox("Role", ["ADMIN", "USER"], index=0 if u["role"] == "ADMIN" else 1)
        active = st.checkbox("Ativo", value=bool(u["active"]))

        ok = st.form_submit_button("Salvar", type="primary")

    if ok:
        # proteção “cara de empresa”
        if me_id == u["id"] and not active:
            st.error("Você não pode desativar a si mesmo.")
            return
        if me_id == u["id"] and role != "ADMIN":
            st.error("Você não pode remover seu próprio ADMIN.")
            return

        update_user(user_id=u["id"], role=role, active=active)
        st.success("Alterações salvas.")
        st.rerun()


@st.dialog("🔑 Resetar senha")
def dialog_reset_password():
    users = list_users()
    if not users:
        st.info("Nenhum usuário encontrado.")
        return

    options = {f'{u["id"]} — {u["email"]}': u for u in users}
    pick = st.selectbox("Selecione o usuário", list(options.keys()))
    u = options[pick]

    with st.form("form_reset_pw"):
        pw1 = st.text_input("Nova senha", type="password")
        pw2 = st.text_input("Confirmar nova senha", type="password")
        ok = st.form_submit_button("Resetar", type="primary")

    if ok:
        if not _pw_ok(pw1):
            st.error("Senha deve ter pelo menos 8 caracteres.")
            return
        if pw1 != pw2:
            st.error("As senhas não conferem.")
            return

        set_password(user_id=u["id"], new_password=pw1)
        st.success("Senha resetada.")
        st.rerun()


# ---------- Page content ----------
colA, colB, colC = st.columns(3)
with colA:
    if st.button("➕ Criar usuário", use_container_width=True):
        dialog_create_user()

with colB:
    if st.button("✏️ Editar usuário", use_container_width=True):
        dialog_edit_user()

with colC:
    if st.button("🔑 Resetar senha", use_container_width=True):
        dialog_reset_password()

st.divider()

q = (st.text_input("Buscar por e-mail", placeholder="ex: user@empresa.com") or "").strip().lower()
users = list_users()
if q:
    users = [u for u in users if q in (u["email"] or "").lower()]

st.subheader("Lista de usuários")

try:
    st.dataframe(users, use_container_width=True)
except TypeError:
    st.dataframe(users, width="stretch")
