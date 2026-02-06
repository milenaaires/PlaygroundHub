import pandas as pd
from src.core.db import connect


def get_compliance_data():
    conn = connect()

    # Query para Conversas Reais (Agrupando para somar tokens de User + Assistant)
    query_conversas = """
    SELECT
        c.id,
        MAX(m.created_at) as "Data/Hora",
        u.email as "Usuário",
        u.role as "Acesso",
        a.name as "Agente",
        c.conversation_topic_summary as "Resumo",
        SUM(m.tokens) as "Tokens", -- SOMA PRECISA DE INPUT + OUTPUT
        a.model as "Modelo",
        MAX(CAST(m.has_attachment AS INT)) as "Tem Anexo?",
        MAX(m.attachment_filename) as "Arquivo"
    FROM chats c
    JOIN chat_messages m ON m.chat_id = c.id
    JOIN users u ON c.user_id = u.id
    JOIN agents a ON c.agent_id = a.id
    GROUP BY c.id, u.email, u.role, a.name, c.conversation_topic_summary, a.model
    ORDER BY "Data/Hora" DESC
    """

    # Query para Mensagens de Teste
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
    WHERE t.role = 'user' -- Se o seu log de teste já registra o total no registro do user
    ORDER BY t.created_at DESC
    """

    try:
        df = pd.read_sql_query(query_conversas, conn)
        df["Origem"] = "Conversa"

        df_test = pd.read_sql_query(query_testes, conn)
        df_test["Origem"] = "Teste"

        # --- PROCESSAMENTO DOS DADOS ---
        df = pd.concat([df, df_test], ignore_index=True)

        if not df.empty:
            df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])
            df["Tokens"] = df["Tokens"].fillna(0).astype(int)
            df["Tem Anexo?"] = df["Tem Anexo?"].astype(bool)
            df["Resumo"] = (
                df["Resumo"].fillna("(Tópico não sumarizado)").astype(str).str.strip()
            )

            # Categorização simples
            def _categorizar(txt):
                txt = str(txt).lower()
                if "teste" in txt:
                    return "Teste"
                if "código" in txt or "code" in txt:
                    return "Dev"
                return "Geral"

            df["Categoria (IA)"] = df["Resumo"].apply(_categorizar)

            df = df.sort_values("Data/Hora", ascending=False).reset_index(drop=True)

        return df
    finally:
        conn.close()
