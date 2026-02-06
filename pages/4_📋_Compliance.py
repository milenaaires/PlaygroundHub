import streamlit as st
import pandas as pd
from datetime import datetime

# --- IMPORTS DO PROJETO ---
try:
    from src.core.ui import sidebar_status
    from src.repos.compliance_repo import get_compliance_data

    # NOVOS IMPORTS DE SEGURANÇA
    from src.auth.rbac import require_roles, ROLE_COMPLIANCE, ROLE_ADMIN
except ImportError:
    st.error(
        "Erro de importação: Verifique se os arquivos em src/auth/ e src/repos/ existem."
    )
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Compliance", page_icon="📋", layout="wide")
sidebar_status()

# --- VERIFICAÇÃO DE ACESSO (RBAC) ---
# Isso vai parar a execução (st.stop()) se o usuário não tiver o papel necessário.
# ROLE_ADMIN também para que você (Admin) consiga testar/debugar.
require_roles({ROLE_COMPLIANCE, ROLE_ADMIN})

st.title("🛡️ Painel de Compliance")
st.markdown("Monitoramento de auditoria baseada em tópicos (Privacy-First).")


# --- LOAD DATA ---
@st.cache_data(ttl=15)
def carregar_dados():
    df = get_compliance_data()
    if df.empty:
        return df

    def estimar_custo(row):
        modelo = str(row["Modelo"]).lower()
        tokens = row["Tokens"]

        # Preços médios por 1k tokens (considerando mix de input/output)
        if "gpt-4" in modelo:
            custo_por_1k = 0.03
        elif "gpt-3.5" in modelo:
            custo_por_1k = 0.0015
        elif "claude-3" in modelo:
            custo_por_1k = 0.015
        else:
            custo_por_1k = 0.001

        return (tokens / 1000) * custo_por_1k

    df["Custo ($)"] = df.apply(estimar_custo, axis=1)

    df["Custo ($)"] = df.apply(estimar_custo, axis=1)
    return df


df_full = carregar_dados()

if df_full.empty:
    st.warning("Sem dados de auditoria no momento.")
    st.stop()

# ==============================================================================
# 1. FILTROS (TOPO)
# ==============================================================================
with st.container(border=True):
    st.markdown("### 🔍 Filtros")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        sel_users = st.multiselect("Usuário", options=df_full["Usuário"].unique())

    with c2:
        if sel_users:
            avail_agents = df_full[df_full["Usuário"].isin(sel_users)][
                "Agente"
            ].unique()
        else:
            avail_agents = df_full["Agente"].unique()
        sel_agents = st.multiselect("Agente", options=avail_agents)
    with c3:
        min_date = df_full["Data/Hora"].min().date()
        date_range = st.date_input(
            "Período", value=(min_date, datetime.now()), format="DD/MM/YYYY"
        )
    with c4:
        only_att = st.checkbox("Com Anexos", value=False)
    with c5:
        origens = (
            df_full["Origem"].unique().tolist() if "Origem" in df_full.columns else []
        )
        options_origem = ["Todos"] + origens
        sel_origem = st.selectbox("Origem", options=options_origem, index=0)

# --- APLICAR FILTROS ---
df_filtered = df_full.copy()

if sel_users:
    df_filtered = df_filtered[df_filtered["Usuário"].isin(sel_users)]
if sel_agents:
    df_filtered = df_filtered[df_filtered["Agente"].isin(sel_agents)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    s, e = date_range
    df_filtered = df_filtered[
        (df_filtered["Data/Hora"].dt.date >= s)
        & (df_filtered["Data/Hora"].dt.date <= e)
    ]
if only_att:
    df_filtered = df_filtered[df_filtered["Tem Anexo?"] == True]
if "Origem" in df_filtered.columns and sel_origem and sel_origem != "Todos":
    df_filtered = df_filtered[df_filtered["Origem"] == sel_origem]

# ==============================================================================
# 2. GRÁFICOS E KPI (CORRIGIDO: GRÁFICO AGORA APARECE SEMPRE)
# ==============================================================================
st.divider()

# Título dinâmico da seção
if len(sel_users) == 1:
    titulo_secao = f"📊 Análise: {sel_users[0]}"
elif len(sel_agents) == 1:
    titulo_secao = f"📊 Análise: Agente {sel_agents[0]}"
else:
    titulo_secao = "📊 Visão Geral"

st.subheader(titulo_secao)

# Colunas: KPIs na Esquerda, Gráfico na Direita
col_kpi, col_chart = st.columns([1, 2])

with col_kpi:
    total_tok = df_filtered["Tokens"].sum()
    total_money = df_filtered["Custo ($)"].sum()
    count_msg = len(df_filtered)

    st.metric("Total Tokens", f"{total_tok:,.0f}")
    st.metric("Custo Estimado", f"$ {total_money:.4f}")
    st.metric("Total Interações", count_msg)

with col_chart:
    # Lógica do Gráfico: Agrupa por dia e soma tokens
    if not df_filtered.empty:
        chart_data = df_filtered.copy()
        chart_data["Dia"] = chart_data["Data/Hora"].dt.date

        # Agrupa e reseta index para o Streamlit entender
        daily_usage = chart_data.groupby("Dia")["Tokens"].sum().reset_index()

        st.caption("Evolução de uso de Tokens (Diário)")
        st.bar_chart(daily_usage, x="Dia", y="Tokens", color="#FF4B4B")
    else:
        st.info("Sem dados para gerar gráfico.")

# ==============================================================================
# 3. TABELA
# ==============================================================================
st.divider()
st.subheader("📋 Detalhamento")

event = st.dataframe(
    df_filtered,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Data/Hora": st.column_config.DatetimeColumn(format="DD/MM/YY HH:mm"),
        "Custo ($)": st.column_config.NumberColumn(format="$ %.5f"),
        "Tem Anexo?": st.column_config.CheckboxColumn(label="📎"),
        "Resumo": st.column_config.TextColumn(width="large", label="Tópico (Teor)"),
        "Tokens": st.column_config.ProgressColumn(
            format="%d", min_value=0, max_value=4000
        ),
        "Acesso": st.column_config.TextColumn(label="Role"),
        "Origem": st.column_config.TextColumn(label="Origem"),
        # Ocultos
        "Arquivo": None,
        "id": None,
        "Agente": None,
        "Modelo": None,
        "Categoria (IA)": None,
    },
    hide_index=True,
)


# ==============================================================================
# 4. POPUP
# ==============================================================================
@st.dialog("Detalhes da Auditoria", width="large")
def show_popup(row):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(row["Agente"])
        st.caption(
            f"Usuário: {row['Usuário']} ({row['Acesso']})"
        )  # Mostra Role no popup tb
    with c2:
        st.metric("Custo", f"$ {row['Custo ($)']:.5f}")

    st.divider()

    st.markdown("#### 📝 Resumo do Tópico")
    st.info(row["Resumo"])

    if row["Tem Anexo?"]:
        st.markdown("#### 📎 Arquivo Detectado")
        with st.container(border=True):
            st.code(row["Arquivo"], language="text")

    st.caption(
        f"Modelo: {row['Modelo']} | Tokens: {row['Tokens']} | Data: {row['Data/Hora']}"
    )


if len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    show_popup(df_filtered.iloc[idx])
