import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- IMPORTS DO PROJETO (src) ---
# Tenta importar a UI padrão do seu time. Se der erro (testando local), ignora.
try:
    from src.core.ui import sidebar_status
except ImportError:
    # Função dummy caso você esteja testando fora da estrutura do projeto
    def sidebar_status():
        st.sidebar.info("Modo de Teste (Sem src.core.ui)")


# --- 1. CONFIGURAÇÃO DA PÁGINA ---
# Em multipage apps, isso define o título da aba do navegador para ESTA página
st.set_page_config(page_title="Compliance & Auditoria", page_icon="🛡️", layout="wide")

# --- 2. INTEGRAÇÃO COM SIDEBAR DO TIME ---
# Chama a função que exibe o status do usuário na barra lateral (igual ao app.py)
sidebar_status()

# --- 3. TÍTULO E CABEÇALHO ---
st.title("🛡️ Painel de Compliance")
st.markdown("Auditoria de prompts, análise de custos e verificação de segurança.")
st.divider()


# --- 4. CAMADA DE DADOS (MOCK) ---
# Mantenha o mock até seu colega liberar a query do banco
@st.cache_data
def carregar_dados_mock():
    usuarios = [
        "alice@empresa.com",
        "bob@empresa.com",
        "carol@empresa.com",
        "dave@dev.com",
    ]
    categorias_possiveis = [
        "Review de Código",
        "Tradução",
        "Criação de Content",
        "Dúvida Técnica",
    ]

    dados = []
    data_hoje = datetime.now()

    for i in range(50):
        data_rand = data_hoje - timedelta(days=np.random.randint(0, 30))
        usuario = np.random.choice(usuarios)
        tokens = np.random.randint(50, 4000)
        tem_anexo = np.random.choice([True, False], p=[0.2, 0.8])
        categoria = np.random.choice(categorias_possiveis)

        # Simulando texto
        if categoria == "Review de Código":
            full_text = f"Review requested by {usuario}:\ndef process(x): return x*2..."
        elif categoria == "Tradução":
            full_text = "Translate the attached legal doc..."
        else:
            full_text = "How do I access the VPN?"

        dados.append(
            {
                "ID": i,
                "Data/Hora": data_rand,
                "Usuário": usuario,
                "Tokens": tokens,
                "Custo ($)": tokens * 0.00002,
                "Tem Anexo?": tem_anexo,
                "Categoria (IA)": categoria,
                "Conteúdo Completo": full_text,
            }
        )

    return pd.DataFrame(dados)


df = carregar_dados_mock()


# --- 5. FUNÇÃO DO POPUP (DIALOG) ---
@st.dialog("Detalhes da Auditoria", width="large")
def mostrar_detalhes(row_data, full_df):
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Usuário")
        st.subheader(row_data["Usuário"])
    with col_b:
        st.caption("Data")
        st.subheader(pd.to_datetime(row_data["Data/Hora"]).strftime("%d/%m/%Y %H:%M"))

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**📝 Teor da Conversa:**")
        st.info(row_data["Conteúdo Completo"])

    with col2:
        st.markdown("**Metadados:**")
        if row_data["Tem Anexo?"]:
            st.warning("⚠️ Contém Anexo")
        else:
            st.success("Sem anexos")
        st.metric("Tokens", row_data["Tokens"])
        st.metric("Custo", f"$ {row_data['Custo ($)']:.4f}")

    st.divider()
    st.subheader(f"📈 Uso Recente: {row_data['Usuário']}")
    user_history = full_df[full_df["Usuário"] == row_data["Usuário"]].copy()
    user_history["Data"] = pd.to_datetime(user_history["Data/Hora"]).dt.date
    daily_usage = user_history.groupby("Data")["Tokens"].sum().reset_index()
    st.bar_chart(daily_usage, x="Data", y="Tokens", color="#FF4B4B")


# --- 6. FILTROS ---
with st.sidebar:
    st.header("🔍 Filtros")  # Adicionado dentro do contexto sidebar para organizar
    usuarios_selecionados = st.multiselect(
        "Usuários", options=df["Usuário"].unique(), default=df["Usuário"].unique()
    )
    data_inicio = st.date_input("Início", value=df["Data/Hora"].min())
    data_fim = st.date_input("Fim", value=datetime.now())
    apenas_com_anexos = st.checkbox("Com anexos")

# Aplicação dos filtros
df_filtrado = df.copy()
df_filtrado["Data/Hora"] = pd.to_datetime(df_filtrado["Data/Hora"])

if usuarios_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Usuário"].isin(usuarios_selecionados)]

df_filtrado = df_filtrado[
    (df_filtrado["Data/Hora"].dt.date >= data_inicio)
    & (df_filtrado["Data/Hora"].dt.date <= data_fim)
]

if apenas_com_anexos:
    df_filtrado = df_filtrado[df_filtrado["Tem Anexo?"] == True]

# --- 7. TABELA ---
st.subheader("📋 Histórico de Prompts")
event = st.dataframe(
    df_filtrado,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Data/Hora": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
        "Custo ($)": st.column_config.NumberColumn(format="$ %.4f"),
        "Tem Anexo?": st.column_config.CheckboxColumn(label="📎"),
        "Tokens": st.column_config.ProgressColumn(
            format="%d", min_value=0, max_value=4000
        ),
        "Conteúdo Completo": st.column_config.TextColumn(
            width="small", label="Preview"
        ),
        "ID": None,
    },
    hide_index=True,
)

if len(event.selection.rows) > 0:
    selected_index = event.selection.rows[0]
    selected_row = df_filtrado.iloc[selected_index]
    mostrar_detalhes(selected_row, df)
