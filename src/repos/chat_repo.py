from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.db import connect


def create_chat(user_id: int, agent_id: int, title: Optional[str] = None) -> int:
    """Cria um novo chat para o agente. title opcional (ex.: 'Chat 02/02/2025')."""
    if not title:
        title = f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chats (user_id, agent_id, title) VALUES (?, ?, ?)",
        (user_id, agent_id, title),
    )
    conn.commit()
    chat_id = cur.lastrowid
    conn.close()
    return chat_id


def list_chats(user_id: int, agent_id: int) -> List[Dict[str, Any]]:
    """Lista chats do usuário para um agente (mais recentes primeiro)."""
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, title, created_at FROM chats
           WHERE user_id = ? AND agent_id = ? ORDER BY created_at DESC""",
        (user_id, agent_id),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r["id"], "title": r["title"], "created_at": r["created_at"]}
        for r in rows
    ]


def get_messages(chat_id: int) -> List[Dict[str, Any]]:
    """Mensagens de um chat (ordem cronológica)."""
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM chat_messages WHERE chat_id = ? ORDER BY id",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def add_message(chat_id: int, role: str, content: str) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content),
    )
    conn.commit()
    conn.close()
