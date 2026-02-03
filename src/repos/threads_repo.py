from datetime import datetime
from typing import Optional, Dict, Any

from ..core.db import connect


def create_thread(user_id: int, agent_id: int) -> int:
    title = f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO chats (user_id, agent_id, title) VALUES (?, ?, ?)',
        (user_id, agent_id, title),
    )
    conn.commit()
    thread_id = cur.lastrowid
    conn.close()
    return thread_id


def get_thread(user_id: int, thread_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT id as thread_id, user_id, agent_id, previous_response_id, created_at '
        'FROM chats WHERE id = ? AND user_id = ?',
        (thread_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_thread_by_agent(user_id: int, agent_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT id as thread_id, user_id, agent_id, previous_response_id, created_at '
        'FROM chats WHERE user_id = ? AND agent_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id, agent_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_previous_response_id(
    user_id: int,
    thread_id: int,
    previous_response_id: Optional[str],
):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'UPDATE chats SET previous_response_id = ? WHERE id = ? AND user_id = ?',
        (previous_response_id, thread_id, user_id),
    )
    conn.commit()
    conn.close()
