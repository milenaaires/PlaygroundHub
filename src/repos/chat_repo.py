from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..core.db import connect


def create_chat(user_id: int, agent_id: int, title: Optional[str] = None) -> int:
    """Cria um novo chat para o agente. title opcional (ex.: 'Chat 02/02/2025')."""
    if not title:
        title = f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    default_topic_summary = "Novo chat iniciado."
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chats (user_id, agent_id, title, conversation_topic_summary) VALUES (?, ?, ?, ?)",
        (user_id, agent_id, title, default_topic_summary),
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
        """SELECT id, title, created_at, updated_at FROM chats
           WHERE user_id = ? AND agent_id = ? ORDER BY updated_at DESC, created_at DESC""",
        (user_id, agent_id),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r["id"], "title": r["title"], "created_at": r["created_at"], "updated_at": r["updated_at"]}
        for r in rows
    ]


def get_messages(chat_id: int) -> List[Dict[str, Any]]:
    """Mensagens de um chat (ordem cronológica)."""
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content, tokens FROM chat_messages WHERE chat_id = ? ORDER BY id",
        (chat_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "tokens": r["tokens"]} for r in rows]


def add_message(
    chat_id: int,
    role: str,
    content: str,
    tokens: Optional[int] = None,
    has_attachment: Optional[bool] = None,
    attachment_filename: Optional[str] = None,
) -> None:
    conn = connect()
    cur = conn.cursor()
    try:
        tokens_value = int(tokens) if tokens is not None else 0
    except (TypeError, ValueError):
        tokens_value = 0

    filename_value = (attachment_filename or "").strip() or None
    if filename_value:
        # `Path(...).name` is OS-specific. On Linux, a Windows path like
        # "C:\tmp\file.pdf" doesn't get split on "\". Normalize separators so we
        # persist only the basename across platforms.
        filename_value = Path(filename_value.replace("\\", "/")).name[:200] or None
    has_attachment_value = bool(has_attachment) if has_attachment is not None else bool(filename_value)
    cur.execute(
        "INSERT INTO chat_messages (chat_id, role, content, tokens, has_attachment, attachment_filename) VALUES (?, ?, ?, ?, ?, ?)",
        (chat_id, role, content, tokens_value, 1 if has_attachment_value else 0, filename_value),
    )
    cur.execute("UPDATE chats SET updated_at = datetime('now') WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()



def get_chat(chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, agent_id, title, conversation_topic_summary, previous_response_id, created_at, updated_at FROM chats WHERE id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_conversation_topic_summary(
    chat_id: int,
    user_id: int,
    conversation_topic_summary: Optional[str],
) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chats SET conversation_topic_summary = ? WHERE id = ? AND user_id = ?",
        (conversation_topic_summary, chat_id, user_id),
    )
    conn.commit()
    conn.close()


def update_previous_response_id(chat_id: int, user_id: int, previous_response_id: Optional[str]) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chats SET previous_response_id = ? WHERE id = ? AND user_id = ?",
        (previous_response_id, chat_id, user_id),
    )
    conn.commit()
    conn.close()


def rename_chat(chat_id: int, user_id: int, title: str) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE chats SET title = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
        (title, chat_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_chat(chat_id: int, user_id: int) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM chat_messages WHERE chat_id = ?",
        (chat_id,),
    )
    cur.execute(
        "DELETE FROM chats WHERE id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    conn.commit()
    conn.close()


def add_chat_test_message(
    user_id: int,
    role: str,
    content: str,
    agent_id: Optional[int] = None,
    tokens: Optional[int] = None,
    has_attachment: bool = False,
    attachment_filename: Optional[str] = None,
    model: Optional[str] = None,
    agent_name: Optional[str] = None,
) -> None:
    """Persiste mensagem do Chat Testes para auditoria no Compliance."""
    conn = connect()
    cur = conn.cursor()
    tokens_val = int(tokens) if tokens is not None else 0
    fn = (attachment_filename or "").strip() or None
    if fn:
        fn = Path(fn.replace("\\", "/")).name[:200] or None
    cur.execute(
        """INSERT INTO chat_test_messages (user_id, agent_id, role, content, tokens, has_attachment, attachment_filename, model, agent_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, agent_id, role, content, tokens_val, 1 if has_attachment else 0, fn, model, agent_name),
    )
    conn.commit()
    conn.close()
