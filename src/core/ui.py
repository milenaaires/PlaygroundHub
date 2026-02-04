import streamlit as st

APP_NAME = "PlaygroundHub"


def page_header(page_name: str, title=None, subtitle=None):
    """
    Menu superior: breadcrumb (App > Página) + título + subtítulo.
    Ex.: page_header("User", title="Área do usuário", subtitle="Agentes e chat")
    """
    display_title = title or page_name
    st.markdown(
        """
    <style>
        /* Barra superior tipo breadcrumb */
        div[data-testid="stMarkdown"] + div[data-testid="stVerticalBlock"] .stMarkdown:first-child p,
        .breadcrumb-top { font-size: 0.9rem !important; opacity: 0.9 !important; margin-bottom: 0.2rem !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="breadcrumb-top" style="color: var(--text-color); font-size: 0.9rem; opacity: 0.88; margin-bottom: 0.15rem;">'
        f'<strong>{APP_NAME}</strong> &nbsp;&gt;&nbsp; {page_name}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {display_title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)


def sidebar_status(logo_path="assets/Logo.png"):
    # Sidebar: tamanho de texto + card do usuário (estilo MOVEdot: avatar, nome, email, Sair)
    st.markdown(
        """
    <style>
        /* Sidebar cabe na tela, sem rolagem; menos padding interno */
        [data-testid="stSidebar"] {
            max-height: 100vh !important;
            overflow: hidden !important;
        }
        /* Tudo mais para cima: menos padding no topo/baixo da sidebar */
        [data-testid="stSidebar"] > div:first-child { padding-top: 0.1rem !important; padding-bottom: 0.1rem !important; }
        /* Menos espaço entre blocos da sidebar */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { padding-top: 0.0rem !important; padding-bottom: 0.0rem !important; }
        /* Logo na sidebar: pouco espaço em cima/embaixo */
        [data-testid="stSidebar"] img { max-height: 150px !important; width: auto !important; object-fit: contain !important; margin: 0rem 0 !important; display: block !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] { margin: 0 !important; padding: 0 !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] + div { margin-top: 0 !important; }
        [data-testid="stSidebar"] a { font-size: 2rem !important; }
        [data-testid="stSidebar"] .stMarkdown { font-size: 0.95rem !important; }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { font-size: 0.95rem !important; }
        /* Linhas horizontais: mínimo espaço em cima/embaixo */
        [data-testid="stSidebar"] hr { margin: 0rem 0 !important; }
        .sidebar-user-card {
            background: var(--secondary-background-color);
            border-radius: 10px;
            padding: 0.35rem 0.5rem;
            margin: 0.2rem 0;
            display: flex;
            align-items: top;
            gap: 8px;
        }
        .sidebar-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #E63946;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1rem;
            flex-shrink: 0;
        }
        .sidebar-user-info { flex: 1; min-width: 0; }
        /* Nome: altere font-size, margin aqui */
        .sidebar-user-name { font-weight: 600; font-size: 0.6rem; margin: 0 0 1px 0; color: var(--text-color); }
        /* E-mail: altere font-size aqui */
        .sidebar-user-email { font-size: 0.2rem; opacity: 0.85; margin: 0; word-break: break-all; }
        /* Role (USER/ADMIN): altere font-size, padding aqui */
        .sidebar-role-pill {
            display: inline-block;
            background: #2e7d32;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.3rem;
            font-weight: 500;
            margin-top: 1px;
        }
        /* Botão Sair: vermelho */
        [data-testid="stSidebar"] .stButton > button {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            background: #c62828 !important;
            color: white !important;
            border: 1px solid #b71c1c !important;
            border-radius: 6px !important;
            padding: 0.35rem 0.6rem !important;
            margin-top: 4px !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #b71c1c !important;
            border-color: #8e0000 !important;
            color: white !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        try:
            st.image(logo_path, use_container_width=True)
        except Exception:
            pass

        st.divider()

        if st.session_state.get("authenticated"):
            email = st.session_state.get("email", "")
            role = (st.session_state.get("role") or "USER").upper()
            # Nome: parte antes do @ ou "Usuário"
            display_name = email.split("@")[0].replace(".", " ").title() if email else "Usuário"
            initial = (display_name[0] if display_name else "U").upper()
            st.markdown(
                f"""
            <div class="sidebar-user-card">
                <div class="sidebar-avatar">{initial}</div>
                <div class="sidebar-user-info">
                    <p class="sidebar-user-name">{display_name}</p>
                    <p class="sidebar-user-email">{email}</p>
                    <span class="sidebar-role-pill">{role}</span>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True)
            if st.button("Sair (Logout)", key="sidebar_logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        else:
            st.caption("Não autenticado")
        st.divider()
