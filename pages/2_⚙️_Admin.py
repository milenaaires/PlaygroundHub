import streamlit as st
from src.auth.rbac import require_roles, ROLE_ADMIN
from src.repos.users_repo import list_users, create_user, update_user, set_password
from src.core.ui import sidebar_status, page_header

sidebar_status()
require_roles({ROLE_ADMIN})

page_header("Admin", title="Admin – Usuários", subtitle="Gerencie usuários e papéis.")

search = st.text_input("Buscar por e-mail", placeholder="ex: user@empresa.com").strip().lower()

users = list_users()
users = [u for u in users if search in u["email"]]
st.subheader("Lista de usuários")
st.dataframe(
    [{ "id": u["id"], "email": u["email"], "role": u["role"], "active": bool(u["active"]) } for u in users],
    use_container_width=True
)
# Criar usuário

import streamlit as st

with st.form("create_user"):
    new_email = st.text_input("E-mail (novo usuário)").strip().lower()
    new_role = st.selectbox("Role", ["ADMIN", "USER", "COMPLIANCE"])
    new_password = st.text_input("Senha inicial", type="password")
    submitted = st.form_submit_button("Criar usuário", type="primary")

if submitted:
    if "@" not in new_email or "." not in new_email:
        st.error("E-mail inválido.")
        st.stop()

    if len(new_password) < 8:
        st.error("A senha precisa ter pelo menos 8 caracteres.")
        st.stop()

    create_user(new_email, new_password, new_role, active=True)
    st.success("Usuário criado com sucesso!")
    st.rerun()

st.divider()
st.subheader("Editar usuário")

user_ids = [u["id"] for u in users]
selected_id = st.selectbox("Selecione o ID do usuário", user_ids)

selected_user = next(u for u in users if u["id"] == selected_id)

edit_email = st.text_input("E-mail", value=selected_user["email"], key="edit_email")
edit_role = st.selectbox("Role", ["ADMIN", "USER", "COMPLIANCE"], index=["ADMIN","USER","COMPLIANCE"].index(selected_user["role"]), key="edit_role")
edit_active = st.checkbox("Ativo", value=bool(selected_user["active"]), key="edit_active")

if st.button("Salvar alterações"):
    # proteção simples: não desativar a si mesmo
    if selected_id == st.session_state.get("user_id") and not edit_active:
        st.error("Você não pode desativar a si mesmo.")
    else:
        update_user(selected_id, email=edit_email, role=edit_role, active=edit_active)
        st.success("Usuário atualizado.")
        st.rerun()

st.subheader("Resetar senha")
reset_pass = st.text_input("Nova senha", type="password", key="reset_pass")
if st.button("Resetar senha do usuário"):
    if not reset_pass:
        st.error("Digite a nova senha.")
    else:
        set_password(selected_id, reset_pass)
        st.success("Senha atualizada.")
        st.rerun()
