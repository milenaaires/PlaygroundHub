import streamlit as st
from src.repos.users_repo import get_user_by_email
from src.auth.auth import verify_password

st.title("Login")

email = st.text_input("E-mail")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    user = get_user_by_email(email)
    if not user:
        st.error("Usuário não encontrado.")
        st.stop()

    if not user["active"]:
        st.error("Usuário desativado.")
        st.stop()

    if not verify_password(password, user["password_hash"]):
        st.error("Senha incorreta.")
        st.stop()

    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["email"] = user["email"]
    st.session_state["role"] = user["role"]

    st.success("Login realizado!")
    st.rerun()

if st.session_state.get("authenticated"):
    st.info(f"Logado como: {st.session_state.get('email')} ({st.session_state.get('role')})")
    if st.button("Logout"):
        for k in ["authenticated", "user_id", "email", "role"]:
            st.session_state.pop(k, None)
        st.rerun()
