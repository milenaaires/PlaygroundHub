import streamlit as st

def sidebar_status(logo_path="assets/logo.png"):
    with st.sidebar:
        try:
            st.image(logo_path, use_container_width=True)
        except Exception:
            pass

        st.divider()

        if st.session_state.get("authenticated"):
            email = st.session_state.get("email", "")
            role = st.session_state.get("role", "")
            st.markdown(f"### 👤 {email}")
            st.markdown(f"**Role:** `{role}`")
        else:
            st.caption("Não autenticado")
        st.divider()
