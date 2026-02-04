import pandas as pd
from src.core.db import connect


def get_compliance_data():
    conn = connect()

    # AJUSTE NA QUERY:
    # 1. Adicionado u.role as "Acesso" (Vem da tabela users)
    # 2. Mantido m.role apenas para filtro interno (WHERE)
    query = """
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
    WHERE m.role = 'user' -- Mantemos filtro para pegar msg enviada pelo humano
    ORDER BY m.created_at DESC
    """

    try:
        df = pd.read_sql_query(query, conn)

        if not df.empty:
            df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])
            df["Tokens"] = df["Tokens"].fillna(0).astype(int)

            if "Tem Anexo?" in df.columns:
                df["Tem Anexo?"] = df["Tem Anexo?"].fillna(0).astype(int).astype(bool)

            df["Arquivo"] = df["Arquivo"].fillna("")
            df["Resumo"] = df["Resumo"].fillna("").astype(str).str.strip()
            df.loc[df["Resumo"] == "", "Resumo"] = "(Tópico não sumarizado)"

            # Categorização simples para UI
            def _categorizar(txt):
                txt = txt.lower()
                if "teste" in txt:
                    return "Teste"
                if "código" in txt or "code" in txt:
                    return "Dev"
                return "Geral"

            df["Categoria (IA)"] = df["Resumo"].apply(_categorizar)

        return df
    finally:
        conn.close()
