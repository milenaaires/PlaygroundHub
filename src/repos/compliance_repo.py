import pandas as pd
from src.core.db import connect


def get_compliance_data():
    conn = connect()

    query_conversas = """
    SELECT
        m.id,
        m.created_at as "Data/Hora",
        u.email as "Usuário",
        u.role as "Acesso",
        a.name as "Agente",
        c.conversation_topic_summary as "Resumo",
        m.tokens as "Tokens",
        a.model as "Modelo",
        m.has_attachment as "Tem Anexo?",
        m.attachment_filename as "Arquivo"
    FROM chat_messages m
    JOIN chats c ON m.chat_id = c.id
    JOIN users u ON c.user_id = u.id
    JOIN agents a ON c.agent_id = a.id
    WHERE m.role = 'user'
    ORDER BY m.created_at DESC
    """

    query_testes = """
    SELECT
        t.id,
        t.created_at as "Data/Hora",
        u.email as "Usuário",
        u.role as "Acesso",
        COALESCE(a.name, t.agent_name, '(Em configuração)') as "Agente",
        '(Chat Testes)' as "Resumo",
        t.tokens as "Tokens",
        COALESCE(a.model, t.model, '—') as "Modelo",
        t.has_attachment as "Tem Anexo?",
        t.attachment_filename as "Arquivo"
    FROM chat_test_messages t
    JOIN users u ON t.user_id = u.id
    LEFT JOIN agents a ON t.agent_id = a.id
    WHERE t.role = 'user'
    ORDER BY t.created_at DESC
    """

    try:
        df = pd.read_sql_query(query_conversas, conn)
        df["Origem"] = "Conversa"

        df_test = pd.read_sql_query(query_testes, conn)
        df_test["Origem"] = "Teste"

        if not df.empty:
            df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])
            df["Tokens"] = df["Tokens"].fillna(0).astype(int)
            if "Tem Anexo?" in df.columns:
                df["Tem Anexo?"] = df["Tem Anexo?"].fillna(0).astype(int).astype(bool)
            df["Arquivo"] = df["Arquivo"].fillna("")
            df["Resumo"] = df["Resumo"].fillna("").astype(str).str.strip()
            df.loc[df["Resumo"] == "", "Resumo"] = "(Tópico não sumarizado)"
            def _categorizar(txt):
                txt = str(txt).lower()
                if "teste" in txt:
                    return "Teste"
                if "código" in txt or "code" in txt:
                    return "Dev"
                return "Geral"
            df["Categoria (IA)"] = df["Resumo"].apply(_categorizar)

        if not df_test.empty:
            df_test["Data/Hora"] = pd.to_datetime(df_test["Data/Hora"])
            df_test["Tokens"] = df_test["Tokens"].fillna(0).astype(int)
            if "Tem Anexo?" in df_test.columns:
                df_test["Tem Anexo?"] = df_test["Tem Anexo?"].fillna(0).astype(int).astype(bool)
            df_test["Arquivo"] = df_test["Arquivo"].fillna("")
            df_test["Categoria (IA)"] = "Teste"

        df = pd.concat([df, df_test], ignore_index=True)
        if not df.empty:
            df = df.sort_values("Data/Hora", ascending=False).reset_index(drop=True)
        return df
    finally:
        conn.close()
