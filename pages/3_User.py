import streamlit as st
from src.auth.rbac import require_roles, ROLE_USER, ROLE_ADMIN
from src.core.config import get_settings
from src.repos.agents_repo import (
    create_agent,
    list_agents_by_user,
    get_agent,
    update_agent,
    delete_agent,
)
from src.repos.chat_repo import (
    get_messages,
    add_message,
    create_chat,
    list_chats,
    get_chat,
    update_previous_response_id,
)
from src.agents.service import run_agent_chat
from src.core.db import init_db

from src.core.ui import sidebar_status

sidebar_status()

require_roles({ROLE_USER, ROLE_ADMIN})

st.title("User")

user_id = st.session_state.get("user_id")
if user_id is None:
    st.warning("Faça login para usar os agentes e o chat.")
    st.stop()

# Chat Testes (popup) continua em memória; agentes e histórico "Acessar Chat" vêm do banco
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "user", "content": "Olá!"},
        {"role": "assistant", "content": "Olá! Como posso ajudar você hoje?"},
    ]
if "edit_popup_chat_messages" not in st.session_state:
    st.session_state.edit_popup_chat_messages = [
        {"role": "user", "content": "Olá!"},
        {"role": "assistant", "content": "Olá! Como posso ajudar?"},
    ]

def _ensure_openai_key() -> bool:
    settings = get_settings()
    if not settings.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY nao configurada.")
        return False
    return True



def _render_chat_config_and_messages(prefix=""):
    """Renderiza Chat Config e Chat Messages em colunas (usado dentro do popup)."""
    col_config, col_chat = st.columns([1, 2])
    with col_config:
        st.subheader("Chat Config")
        st.text_input("Agent Name", value="Agent", key=f"{prefix}agent_name")
        st.text_area("Agent Description", value="Agent is a helpful assistant.", key=f"{prefix}agent_desc")
        st.selectbox("Model", options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], key=f"{prefix}model")
        max_tokens = st.slider("Max Tokens", min_value=100, max_value=1000, value=100, step=100, key=f"{prefix}tokens")
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key=f"{prefix}temp")
        st.text_area("System Prompt", value="You are a helpful assistant.", key=f"{prefix}system")
        if st.button("Save Config", use_container_width=True, key=f"{prefix}save"):
            create_agent(
                user_id=user_id,
                name=st.session_state.get(f"{prefix}agent_name", "Agent"),
                description=st.session_state.get(f"{prefix}agent_desc", ""),
                model=st.session_state.get(f"{prefix}model", "gpt-4o"),
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=st.session_state.get(f"{prefix}system", "You are a helpful assistant."),
            )
            st.success("Agente salvo.")
            st.rerun()

    with col_chat:
        st.subheader("Chat Testes")
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {"role": "user", "content": "Olá!"},
                {"role": "assistant", "content": "Olá! Como posso ajudar você hoje?"},
            ]
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        if prompt := st.chat_input("Digite sua mensagem...", key=f"{prefix}chat_input"):
            if not _ensure_openai_key():
                if prefix == "popup_":
                    st.session_state["reopen_popup"] = "config"
                st.rerun()
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            agent_cfg = {
                "name": st.session_state.get(f"{prefix}agent_name", "Agent"),
                "description": st.session_state.get(f"{prefix}agent_desc", ""),
                "model": st.session_state.get(f"{prefix}model", "gpt-4o"),
                "max_tokens": st.session_state.get(f"{prefix}tokens", 100),
                "temperature": st.session_state.get(f"{prefix}temp", 0.5),
                "system_prompt": st.session_state.get(f"{prefix}system", "You are a helpful assistant."),
            }
            prev_key = f"{prefix}prev_response_id"
            prev_id = st.session_state.get(prev_key)
            try:
                with st.spinner("Consultando o agente..."):
                    reply, resp_id = run_agent_chat(
                        agent_cfg,
                        prompt,
                        previous_response_id=prev_id,
                    )
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                st.session_state[prev_key] = resp_id
            except Exception as e:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Erro ao consultar o modelo: {e}",
                })
            if prefix == "popup_":
                st.session_state["reopen_popup"] = "config"
            st.rerun()

# Tamanho do popup: "small" (500px), "medium" (750px), "large" (1280px)
DIALOG_WIDTH = "large"


def _render_access_chat(prefix: str):
    """Acessar Chat: seleção de agente → por agente: Novo chat ou ver histórico de chats."""
    init_db()  # garante que tabelas chats/chat_messages existem (ex.: após atualização do schema)
    saved = list_agents_by_user(user_id)
    if not saved:
        st.warning("Nenhum agente salvo. Use **Configurar Agente** e **Save Config** para criar um.")
        return
    options = [f"{a['name']} (id: {a['id']})" for a in saved]
    idx = st.selectbox(
        "Selecione o agente",
        range(len(saved)),
        format_func=lambda i: options[i],
        key=f"{prefix}agent",
    )
    agent = saved[idx]
    agent_id = agent["id"]

    # Ao trocar de agente, limpa o chat selecionado para mostrar lista de chats desse agente
    key_agent = f"{prefix}access_agent_id"
    key_chat = f"{prefix}access_chat_id"
    if st.session_state.get(key_agent) != agent_id:
        st.session_state[key_agent] = agent_id
        st.session_state.pop(key_chat, None)

    chat_id = st.session_state.get(key_chat)

    if chat_id:
        # Modo conversa: mostra mensagens e input; botão Voltar para lista de chats
        if st.button("← Voltar para lista de chats", key=f"{prefix}back_chats"):
            st.session_state.pop(key_chat, None)
            if prefix == "access_popup_":
                st.session_state["reopen_popup"] = "access_chat"
            st.rerun()
        st.caption(f"Agente: **{agent['name']}** · Modelo: {agent['model']}")
        messages = get_messages(chat_id)
        if not messages:
            add_message(chat_id, "assistant", f"Olá! Sou o agente **{agent['name']}**. Como posso ajudar?")
            messages = get_messages(chat_id)
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        if prompt := st.chat_input("Digite sua mensagem...", key=f"{prefix}input"):
            if not _ensure_openai_key():
                if prefix == "access_popup_":
                    st.session_state["reopen_popup"] = "access_chat"
                st.rerun()
            add_message(chat_id, "user", prompt)
            chat = get_chat(chat_id, user_id)
            prev_id = chat.get("previous_response_id") if chat else None
            try:
                with st.spinner("Consultando o agente..."):
                    reply, resp_id = run_agent_chat(
                        agent,
                        prompt,
                        previous_response_id=prev_id,
                    )
                add_message(chat_id, "assistant", reply)
                update_previous_response_id(chat_id, user_id, resp_id)
            except Exception as e:
                st.error(f"Erro ao consultar o modelo: {e}")
            if prefix == "access_popup_":
                st.session_state["reopen_popup"] = "access_chat"
            st.rerun()

    chats = list_chats(user_id, agent_id)
    if chats:
        st.subheader("Histórico de chats")
        for c in chats:
            with st.container():
                col_info, col_open = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**{c['title']}**")
                    st.caption(c["created_at"])
                with col_open:
                    if st.button("Abrir", key=f"{prefix}open_{c['id']}", use_container_width=True):
                        st.session_state[key_chat] = c["id"]
                        if prefix == "access_popup_":
                            st.session_state["reopen_popup"] = "access_chat"
                        st.rerun()
                st.divider()
    else:
        st.info("Nenhum chat ainda. Clique em **Novo chat** para começar.")


# Popup (Streamlit 1.33+); se não existir dialog, o conteúdo é exibido direto na aba Chat
_dialog_decorator = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

if _dialog_decorator is not None:
    # Diálogo com altura fixa; rolagem no próprio diálogo; campo de mensagem fixo no rodapé do popup
    st.markdown(
        """
    <style>
        div[data-testid="stDialog"] div[role="dialog"] {
            max-height: 85vh !important;
            height: 85vh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }
        /* Campo de digitação fixo no rodapé do popup */
        div[data-testid="stDialog"] div[data-testid="stChatInput"],
        div[data-testid="stDialog"] [data-testid="stChatInput"] {
            position: sticky !important;
            bottom: 0 !important;
            background: var(--background-color) !important;
            z-index: 10 !important;
            padding-bottom: 0.5rem !important;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.06) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    @_dialog_decorator("Configurar e conversar", width=DIALOG_WIDTH)
    def chat_popup():
        _render_chat_config_and_messages(prefix="popup_")

    def _render_edit_agent_popup(agent):
        """Layout igual ao criar agente: coluna esquerda = form de edição, direita = Chat Testes."""
        col_config, col_chat = st.columns([1, 2])
        with col_config:
            st.subheader("Editar agente")
            col_s, col_c = st.columns(2)
            with col_s:
                if st.button("Salvar alterações", use_container_width=True, key="edit_popup_save"):
                    update_agent(
                        agent_id=agent["id"],
                        user_id=user_id,
                        name=st.session_state.get("edit_popup_name", agent.get("name", "Agent")),
                        description=st.session_state.get("edit_popup_desc", agent.get("description", "")),
                        model=st.session_state.get("edit_popup_model", agent.get("model", "gpt-4o")),
                        max_tokens=st.session_state.get("edit_popup_tokens", agent.get("max_tokens", 100)),
                        temperature=float(st.session_state.get("edit_popup_temp", agent.get("temperature", 0.5))),
                        system_prompt=st.session_state.get("edit_popup_system", agent.get("system_prompt", "")),
                    )
                    st.session_state.pop("edit_agent_id", None)
                    st.success("Agente atualizado.")
                    st.rerun()
            with col_c:
                if st.button("Cancelar", use_container_width=True, key="edit_popup_cancel"):
                    st.session_state.pop("edit_agent_id", None)
                    st.session_state["reopen_popup"] = "agents_list"
                    st.rerun()
            st.divider()
            name = st.text_input("Agent Name", value=agent.get("name", "Agent"), key="edit_popup_name")
            description = st.text_area("Agent Description", value=agent.get("description", ""), key="edit_popup_desc")
            model = st.selectbox(
                "Model",
                options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                index=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"].index(agent.get("model", "gpt-4o")),
                key="edit_popup_model",
            )
            max_tokens = st.slider("Max Tokens", min_value=100, max_value=1000, value=agent.get("max_tokens", 100), step=100, key="edit_popup_tokens")
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(agent.get("temperature", 0.5)), step=0.1, key="edit_popup_temp")
            system_prompt = st.text_area("System Prompt", value=agent.get("system_prompt", ""), key="edit_popup_system")

        with col_chat:
            st.subheader("Chat Testes")
            if "edit_popup_chat_messages" not in st.session_state:
                st.session_state.edit_popup_chat_messages = [
                    {"role": "user", "content": "Olá!"},
                    {"role": "assistant", "content": "Olá! Como posso ajudar?"},
                ]
            for msg in st.session_state.edit_popup_chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            if prompt := st.chat_input("Digite sua mensagem...", key="edit_popup_chat_input"):
                if not _ensure_openai_key():
                    st.session_state["reopen_popup"] = "edit_agent"
                    st.rerun()
                st.session_state.edit_popup_chat_messages.append({"role": "user", "content": prompt})
                agent_cfg = {
                    "name": st.session_state.get("edit_popup_name", agent.get("name", "Agent")),
                    "description": st.session_state.get("edit_popup_desc", agent.get("description", "")),
                    "model": st.session_state.get("edit_popup_model", agent.get("model", "gpt-4o")),
                    "max_tokens": st.session_state.get("edit_popup_tokens", agent.get("max_tokens", 100)),
                    "temperature": st.session_state.get("edit_popup_temp", agent.get("temperature", 0.5)),
                    "system_prompt": st.session_state.get("edit_popup_system", agent.get("system_prompt", "")),
                }
                prev_key = "edit_popup_prev_response_id"
                prev_id = st.session_state.get(prev_key)
                try:
                    with st.spinner("Consultando o agente..."):
                        reply, resp_id = run_agent_chat(
                            agent_cfg,
                            prompt,
                            previous_response_id=prev_id,
                        )
                    st.session_state.edit_popup_chat_messages.append({"role": "assistant", "content": reply})
                    st.session_state[prev_key] = resp_id
                except Exception as e:
                    st.session_state.edit_popup_chat_messages.append({
                        "role": "assistant",
                        "content": f"Erro ao consultar o modelo: {e}",
                    })
                st.session_state["reopen_popup"] = "edit_agent"
                st.rerun()

    @_dialog_decorator("Editar agente", width=DIALOG_WIDTH)
    def edit_agent_popup():
        edit_id = st.session_state.get("edit_agent_id")
        if not edit_id:
            return
        agent = get_agent(int(edit_id), user_id)
        if not agent:
            st.session_state.pop("edit_agent_id", None)
            return
        _render_edit_agent_popup(agent)

    @_dialog_decorator("Acessar Chat", width=DIALOG_WIDTH)
    def access_chat_popup():
        _render_access_chat(prefix="access_popup_")

    def _render_agents_list(prefix: str):
        """Lista de agentes com Editar e Excluir (dentro do popup Ver agentes ou inline).
        Nunca chamar outro @st.dialog daqui (Streamlit não permite diálogos aninhados).
        """
        saved = list_agents_by_user(user_id)
        edit_id = st.session_state.get("edit_agent_id")
        if edit_id and _dialog_decorator is not None:
            # Estamos dentro do popup "Ver agentes"; abrir "Editar" no próximo run, não aqui
            st.session_state["reopen_popup"] = "edit_agent"
            st.rerun()
            return
        if edit_id and _dialog_decorator is None:
            agent = get_agent(int(edit_id), user_id)
            if agent is not None:
                st.subheader(f"Editar agente: {agent['name']}")
                with st.form("form_edit_agent", clear_on_submit=False):
                    name = st.text_input("Agent Name", value=agent["name"], key="edit_name")
                    description = st.text_area("Agent Description", value=agent.get("description", ""), key="edit_desc")
                    model = st.selectbox("Model", options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"], index=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"].index(agent.get("model", "gpt-4o")), key="edit_model")
                    max_tokens = st.slider("Max Tokens", min_value=100, max_value=1000, value=agent.get("max_tokens", 100), step=100, key="edit_tokens")
                    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(agent.get("temperature", 0.5)), step=0.1, key="edit_temp")
                    system_prompt = st.text_area("System Prompt", value=agent.get("system_prompt", ""), key="edit_system")
                    col_s, col_c = st.columns(2)
                    with col_s:
                        submitted = st.form_submit_button("Salvar alterações")
                    with col_c:
                        cancel = st.form_submit_button("Cancelar")
                if submitted:
                    update_agent(agent["id"], user_id, name=name, description=description, model=model, max_tokens=max_tokens, temperature=temperature, system_prompt=system_prompt)
                    st.session_state.pop("edit_agent_id", None)
                    st.success("Agente atualizado.")
                    st.rerun()
                if cancel:
                    st.session_state.pop("edit_agent_id", None)
                    st.rerun()
            else:
                st.session_state.pop("edit_agent_id", None)
                st.rerun()
            return

        if not saved:
            st.warning("Nenhum agente salvo. Use **Configurar Agente** e **Save Config** para criar.")
            return
        st.subheader("Agentes criados")
        for i, agent in enumerate(saved):
            with st.container():
                col_info, col_actions = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**{agent['name']}** · {agent.get('model', 'gpt-4o')} · id: {agent['id']}")
                    if agent.get("description"):
                        st.caption(agent["description"][:80] + ("..." if len(agent.get("description", "")) > 80 else ""))
                with col_actions:
                    if st.button("Editar", key=f"{prefix}edit_btn_{agent['id']}", use_container_width=True):
                        st.session_state["edit_agent_id"] = agent["id"]
                        if _dialog_decorator is not None:
                            st.session_state["reopen_popup"] = "edit_agent"
                        st.rerun()
                    if st.button("Excluir", key=f"{prefix}del_btn_{agent['id']}", use_container_width=True):
                        delete_agent(agent["id"], user_id)
                        if _dialog_decorator is not None:
                            st.session_state["reopen_popup"] = "agents_list"
                        st.rerun()
                st.divider()

    @_dialog_decorator("Ver agentes", width=DIALOG_WIDTH)
    def agents_popup():
        _render_agents_list(prefix="agents_popup_")

# Abas principais: Plataform IA + nova aba que abre o popup
tabs = st.tabs(["Plataform IA", "Chat"])
with tabs[0]:
    st.subheader("Plataform IA")

    st.markdown("""
    **Bem-vindo à Plataforma de IA.** Como usuário, você pode criar agentes, conversar com eles e gerenciar seus chats. Use a aba **Chat** para acessar as ações abaixo.
    """)

    st.markdown("#### Funcionalidades disponíveis")

    st.markdown("**1. Configurar Agente**")
    st.markdown("""
    - Criar um **novo agente**: defina nome, descrição, modelo (ex.: GPT-4o), limite de tokens, temperatura e o *system prompt*.
    - **Salvar** o agente no seu perfil para usar depois.
    - **Testar** na mesma tela: um chat de teste permite enviar mensagens e ver respostas antes de usar em conversas reais.
    """)

    st.markdown("**2. Acessar Chat**")
    st.markdown("""
    - Escolher um **agente** já salvo para conversar.
    - **Novo chat**: iniciar uma nova conversa com aquele agente (cada conversa fica separada no histórico).
    - **Histórico de chats**: ver a lista de conversas anteriores daquele agente e **abrir** qualquer uma para continuar.
    - Dentro de um chat: trocar mensagens e usar **Voltar** para retornar à lista de chats do agente.
    """)

    st.markdown("**3. Ver agentes**")
    st.markdown("""
    - Ver a **lista** de todos os agentes que você criou (nome, modelo, id).
    - **Editar** um agente: alterar nome, descrição, modelo, tokens, temperatura e system prompt; ao cancelar, volta para a lista.
    - **Excluir** um agente (as conversas vinculadas também são removidas).
    """)

    st.markdown("---")
    st.markdown("#### Conceitos")
    with st.expander("O que é um agente?"):
        st.markdown("""
        Um **agente** é uma configuração reutilizável: nome, descrição, modelo (ex.: GPT-4o), limite de tokens, temperatura e o *system prompt* que define o comportamento do assistente.
        """)
    with st.expander("O que é o System Prompt?"):
        st.markdown("""
        O **system prompt** é a instrução fixa enviada ao modelo em toda conversa (ex.: *"Você é um assistente técnico e responde em português."*). Ele define o tom e as regras do agente.
        """)

    st.info("Use a aba **Chat** e os botões **Configurar Agente**, **Acessar Chat** e **Ver agentes** para executar essas funcionalidades.")

with tabs[1]:
    st.subheader("Chat")

    # Reabrir popup após enviar mensagem (st.rerun() fecha o diálogo)
    if _dialog_decorator is not None:
        reopen = st.session_state.pop("reopen_popup", None)
        if reopen == "config":
            chat_popup()
        elif reopen == "access_chat":
            access_chat_popup()
        elif reopen == "edit_agent":
            edit_agent_popup()
        elif reopen == "agents_list":
            agents_popup()

    # Três opções: Configurar Agente, Acessar Chat, Ver agentes
    if not st.session_state.get("chat_view") and not st.session_state.get("agents_view"):
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("Configurar Agente", type="primary", use_container_width=True):
                if _dialog_decorator is not None:
                    st.session_state.chat_messages = [
                        {"role": "user", "content": "Olá!"},
                        {"role": "assistant", "content": "Olá! Como posso ajudar você hoje?"},
                    ]
                    chat_popup()
                else:
                    _render_chat_config_and_messages(prefix="tab_")
        with col_btn2:
            if st.button("Acessar Chat", use_container_width=True):
                if _dialog_decorator is not None:
                    access_chat_popup()
                else:
                    st.session_state["chat_view"] = True
                    st.session_state["agents_view"] = False
                    st.session_state.pop("edit_agent_id", None)
                    st.rerun()
        with col_btn3:
            if st.button("Ver agentes", use_container_width=True):
                st.session_state.pop("edit_agent_id", None)  # evita reabrir edit ao mostrar lista
                if _dialog_decorator is not None:
                    agents_popup()
                else:
                    st.session_state["agents_view"] = True
                    st.session_state["chat_view"] = False
                    st.session_state.pop("edit_agent_id", None)
                    st.rerun()
        st.caption("**Configurar Agente:** criar e testar. **Acessar Chat:** escolher agente e ver histórico. **Ver agentes:** listar, editar ou excluir.")

        if _dialog_decorator is None:
            st.divider()
            _render_chat_config_and_messages(prefix="tab_")
    elif st.session_state.get("agents_view"):
        # Ver agentes (inline quando não há popup)
        if st.button("← Voltar", key="back_agents"):
            st.session_state["agents_view"] = False
            st.session_state.pop("edit_agent_id", None)
            st.rerun()
        _render_agents_list(prefix="agents_inline_")
    else:
        # Tela "Acessar Chat" (inline quando não há popup)
        if st.button("← Voltar", key="back_chat"):
            st.session_state["chat_view"] = False
            st.rerun()
        _render_access_chat(prefix="access_")

