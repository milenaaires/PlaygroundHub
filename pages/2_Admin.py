import streamlit as st
from src.auth.rbac import require_roles, ROLE_ADMIN
from src.repos.users_repo import list_users, create_user, update_user, set_password

require_roles({ROLE_ADMIN})

st.title("Admin - Usuários")

users = list_users()
st.subheader("Lista de usuários")
st.dataframe(
    [{ "id": u["id"], "email": u["email"], "role": u["role"], "active": bool(u["active"]) } for u in users],
    use_container_width=True
)

st.divider()
st.subheader("Criar usuário")

new_email = st.text_input("E-mail (novo usuário)", key="new_email")
new_role = st.selectbox("Role", ["ADMIN", "USER", "COMPLIANCE"], key="new_role")
new_pass = st.text_input("Senha inicial", type="password", key="new_pass")

if st.button("Criar"):
    if not new_email or not new_pass:
        st.error("Preencha e-mail e senha.")
    else:
        try:
            create_user(new_email, new_pass, new_role, active=True)
            st.success("Usuário criado.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao criar usuário: {e}")

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
