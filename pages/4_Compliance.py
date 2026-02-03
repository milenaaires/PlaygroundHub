import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- IMPORTS DO PROJETO ---
try:
    from src.core.ui import sidebar_status
    from src.repos.compliance_repo import (
        get_compliance_data,
    )  # <--- Importando o repo real
except ImportError:
    st.error(
        "Erro de importação. Verifique se o arquivo src/repos/compliance_repo.py existe."
    )
    st.stop()

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Compliance & Auditoria", page_icon="🛡️", layout="wide")
sidebar_status()

st.title("🛡️ Painel de Compliance")
st.markdown("Auditoria de prompts reais extraídos do banco de dados `app.db`.")
st.divider()


# --- 2. FUNÇÃO DE CUSTO ---
def calcular_custo(row):
    # Preços estimados por token (Input) - Exemplo
    # Você pode ajustar esses valores conforme a tabela da OpenAI/Anthropic
    model = str(row["Modelo"]).lower()
    tokens = row["Tokens"]

    if "gpt-4" in model:
        return tokens * (2.50 / 1_000_000)  # Ex: $2.50 por 1M tokens
    elif "gpt-3.5" in model:
        return tokens * (0.50 / 1_000_000)
    else:
        return tokens * (0.20 / 1_000_000)  # Preço genérico


# --- 3. CAMADA DE DADOS (REAL) ---
@st.cache_data(ttl=60)  # Cache de 60 segundos para não ficar lento
def carregar_dados_reais():
    df = get_compliance_data()

    if df.empty:
        return df

    # Enriquecimento dos dados (Processamento Python)
    # 1. Identificar anexos (lógica simples baseada em texto, já que não temos tabela de arquivos)
    df["Tem Anexo?"] = df["Conteúdo Completo"].str.contains(
        r"uploaded:|\[FILE\]", case=False, regex=True
    )

    # 2. Calcular Custo
    df["Custo ($)"] = df.apply(calcular_custo, axis=1)

    # 3. Categorização Simples (Dummy Logic)
    # Num cenário real, você passaria isso num LLM. Aqui vamos por palavras-chave.
    def categorizar(txt):
        txt = txt.lower()
        if "def " in txt or "class " in txt or "code" in txt:
            return "Review de Código"
        if "translate" in txt or "traduza" in txt:
            return "Tradução"
        return "Geral/Dúvida"

    df["Categoria (IA)"] = df["Conteúdo Completo"].apply(categorizar)

    return df


df = carregar_dados_reais()

if df.empty:
    st.warning(
        "Nenhum dado encontrado no banco de dados. Comece a usar o chat para gerar registros."
    )
    st.stop()


# --- 4. FUNÇÃO DO POPUP ---
@st.dialog("Detalhes da Auditoria", width="large")
def mostrar_detalhes(row_data, full_df):
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Usuário")
        st.subheader(row_data["Usuário"])
    with col_b:
        st.caption("Data")
        # Garante que é timestamp antes de formatar
        ts = pd.to_datetime(row_data["Data/Hora"])
        st.subheader(ts.strftime("%d/%m/%Y %H:%M"))

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**📝 Prompt do Usuário:**")
        st.info(row_data["Conteúdo Completo"])
        st.caption(f"Modelo Utilizado: `{row_data['Modelo']}`")

    with col2:
        st.markdown("**Métricas:**")
        if row_data["Tem Anexo?"]:
            st.warning("⚠️ Contém Referência a Arquivo")
        else:
            st.success("Texto Puro")

        st.metric("Tokens (Input)", row_data["Tokens"])
        st.metric("Custo Estimado", f"$ {row_data['Custo ($)']:.6f}")

    st.divider()
    st.subheader(f"📈 Atividade Recente: {row_data['Usuário']}")
    user_history = full_df[full_df["Usuário"] == row_data["Usuário"]].copy()
    user_history["Data"] = pd.to_datetime(user_history["Data/Hora"]).dt.date
    daily_usage = user_history.groupby("Data")["Tokens"].sum().reset_index()
    st.bar_chart(daily_usage, x="Data", y="Tokens", color="#FF4B4B")


# --- 5. FILTROS ---
with st.sidebar:
    st.header("🔍 Filtros DB")
    usuarios_selecionados = st.multiselect("Usuários", options=df["Usuário"].unique())

    min_date = df["Data/Hora"].min().date()
    data_inicio = st.date_input("Início", value=min_date)
    data_fim = st.date_input("Fim", value=datetime.now())

# Aplicação
df_filtrado = df.copy()
if usuarios_selecionados:
    df_filtrado = df_filtrado[df_filtrado["Usuário"].isin(usuarios_selecionados)]

df_filtrado = df_filtrado[
    (df_filtrado["Data/Hora"].dt.date >= data_inicio)
    & (df_filtrado["Data/Hora"].dt.date <= data_fim)
]

# --- 6. TABELA ---
st.subheader("📋 Auditoria de Prompts (Live DB)")

event = st.dataframe(
    df_filtrado,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Data/Hora": st.column_config.DatetimeColumn(format="DD/MM/YY HH:mm"),
        "Custo ($)": st.column_config.NumberColumn(format="$ %.6f"),
        "Tem Anexo?": st.column_config.CheckboxColumn(label="📎"),
        "Categoria (IA)": st.column_config.TextColumn(),
        "Tokens": st.column_config.ProgressColumn(
            format="%d", min_value=0, max_value=8000
        ),
        "Conteúdo Completo": st.column_config.TextColumn(
            width="small", label="Preview"
        ),
        "id": None,  # Esconde IDs
        "Modelo": None,
        "role": None,
    },
    hide_index=True,
)

if len(event.selection.rows) > 0:
    selected_index = event.selection.rows[0]
    # Atenção: pegar pelo índice correto do dataframe filtrado
    selected_row = df_filtrado.iloc[selected_index]
    mostrar_detalhes(selected_row, df)
