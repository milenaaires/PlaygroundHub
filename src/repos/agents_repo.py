from typing import Optional, List, Dict, Any
from ..core.db import connect


def create_agent(
    user_id: int,
    name: str,
    description: str,
    model: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str,
) -> int:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO agents (user_id, name, description, model, max_tokens, temperature, system_prompt)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, description, model, max_tokens, temperature, system_prompt),
    )
    conn.commit()
    agent_id = cur.lastrowid
    conn.close()
    return agent_id


def list_agents_by_user(user_id: int) -> List[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, description, model, max_tokens, temperature, system_prompt, created_at FROM agents WHERE user_id = ? ORDER BY id",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_agent(agent_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, name, description, model, max_tokens, temperature, system_prompt, created_at FROM agents WHERE id = ? AND user_id = ?",
        (agent_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_agent(
    agent_id: int,
    user_id: int,
    name: str,
    description: str,
    model: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str,
) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """UPDATE agents SET name = ?, description = ?, model = ?, max_tokens = ?, temperature = ?, system_prompt = ?
           WHERE id = ? AND user_id = ?""",
        (name, description, model, max_tokens, temperature, system_prompt, agent_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_agent(agent_id: int, user_id: int) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_messages WHERE agent_id = ? AND user_id = ?", (agent_id, user_id))
    cur.execute("DELETE FROM agents WHERE id = ? AND user_id = ?", (agent_id, user_id))
    conn.commit()
    conn.close()
