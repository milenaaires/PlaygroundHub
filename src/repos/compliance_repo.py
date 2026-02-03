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
        m.content as "Conteúdo Completo",
        m.tokens as "Tokens",
        a.model as "Modelo",
        m.role
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

        def _resumo(txt: str) -> str:
            txt = txt or ""
            words = len(txt.split())
            chars = len(txt)
            return f"Mensagem com {words} palavras e {chars} caracteres."

        df["Tem Anexo?"] = df["Conteúdo Completo"].str.contains(
            r"uploaded:|\\[FILE\\]", case=False, regex=True
        )
        df["Categoria (IA)"] = df["Conteúdo Completo"].apply(_categorizar)
        df["Resumo"] = df["Conteúdo Completo"].apply(_resumo)

        # Remove o conteúdo completo para não exibir na área de compliance
        df = df.drop(columns=["Conteúdo Completo"])

        return df
    finally:
        conn.close()
