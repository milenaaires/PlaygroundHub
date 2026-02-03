from typing import Optional, Dict, Any
import uuid

from ..core.db import connect


def create_thread(user_id: int, agent_id: str) -> str:
    thread_id = str(uuid.uuid4())
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO chat_threads (thread_id, user_id, agent_id, previous_response_id) '
        'VALUES (?, ?, ?, ?)',
        (thread_id, user_id, agent_id, None),
    )
    conn.commit()
    conn.close()
    return thread_id


def get_thread(user_id: int, thread_id: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM chat_threads WHERE thread_id = ? AND user_id = ?',
        (thread_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_thread_by_agent(user_id: int, agent_id: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT * FROM chat_threads WHERE user_id = ? AND agent_id = ? '
        'ORDER BY updated_at DESC LIMIT 1',
        (user_id, agent_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_previous_response_id(
    user_id: int,
    thread_id: str,
    previous_response_id: Optional[str],
):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'UPDATE chat_threads SET previous_response_id = ?, updated_at = datetime(\'now\') '
        'WHERE thread_id = ? AND user_id = ?',
        (previous_response_id, thread_id, user_id),
    )
    conn.commit()
    conn.close()
