# src/repos/compliance_repo.py
import pandas as pd
from src.core.db import connect


def get_compliance_data():
    """
    Busca todas as mensagens enviadas por usuários, juntando com
    informações de quem enviou (email) e qual modelo foi usado (agent).
    """
    conn = connect()

    query = """
    SELECT
        m.id,
        m.created_at as "Data/Hora",
        u.email as "Usuário",
        c.conversation_topic_summary as "Resumo",
        m.tokens as "Tokens",
        a.model as "Modelo",
        m.role,
        m.has_attachment as "Tem Anexo?",
        m.attachment_filename as "Arquivo"
    FROM chat_messages m
    JOIN chats c ON m.chat_id = c.id
    JOIN users u ON c.user_id = u.id
    JOIN agents a ON c.agent_id = a.id
    WHERE m.role = 'user' -- Compliance geralmente analisa o que o USUÁRIO enviou
    ORDER BY m.created_at DESC
    """

    try:
        df = pd.read_sql_query(query, conn)

        # Converte a coluna de data para datetime
        df["Data/Hora"] = pd.to_datetime(df["Data/Hora"])

        # Tratamento de nulos
        df["Tokens"] = df["Tokens"].fillna(0).astype(int)

        # Deriva metadados sem expor o conteúdo bruto para Compliance
        def _categorizar(txt: str) -> str:
            txt = (txt or "").lower()
            if "def " in txt or "class " in txt or "code" in txt:
                return "Review de Código"
            if "translate" in txt or "traduza" in txt:
                return "Tradução"
            return "Geral/Dúvida"

        df["Resumo"] = df["Resumo"].fillna("").astype(str).str.strip()
        df.loc[df["Resumo"] == "", "Resumo"] = "(resumo do chat indisponível)"

        if "Tem Anexo?" in df.columns:
            df["Tem Anexo?"] = df["Tem Anexo?"].fillna(0).astype(int).astype(bool)

        df["Categoria (IA)"] = df["Resumo"].apply(_categorizar)

        return df
    finally:
        conn.close()
