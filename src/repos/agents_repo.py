from typing import Optional, List, Dict, Any

from ..core.config import get_settings
from ..core.db import connect


def _default_temperature() -> float:
    settings = get_settings()
    try:
        return float(settings.get('OPENAI_TEMPERATURE') or 0.7)
    except (TypeError, ValueError):
        return 0.7


def _default_max_tokens() -> int:
    settings = get_settings()
    try:
        value = settings.get('OPENAI_MAX_OUTPUT_TOKENS') or 1024
        parsed = int(value)
        return parsed if parsed > 0 else 1024
    except (TypeError, ValueError):
        return 1024


def create_agent(
    user_id: int,
    name: str,
    description: Optional[str],
    model: str,
    max_tokens: Optional[int],
    temperature: Optional[float],
    system_prompt: Optional[str],
) -> int:
    if max_tokens is None:
        max_tokens = _default_max_tokens()
    if temperature is None:
        temperature = _default_temperature()

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
        'SELECT id, user_id, name, description, model, max_tokens, temperature, system_prompt, created_at '
        'FROM agents WHERE user_id = ? ORDER BY id',
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_agent(agent_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'SELECT id, user_id, name, description, model, max_tokens, temperature, system_prompt, created_at '
        'FROM agents WHERE id = ? AND user_id = ?',
        (agent_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_agent_by_id(user_id: int, agent_id: int) -> Optional[Dict[str, Any]]:
    return get_agent(agent_id, user_id)


def update_agent(
    agent_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_prompt: Optional[str] = None,
) -> None:
    fields = []
    values = []

    if name is not None:
        fields.append('name = ?')
        values.append(name)
    if description is not None:
        fields.append('description = ?')
        values.append(description)
    if model is not None:
        fields.append('model = ?')
        values.append(model)
    if max_tokens is not None:
        fields.append('max_tokens = ?')
        values.append(max_tokens)
    if temperature is not None:
        fields.append('temperature = ?')
        values.append(temperature)
    if system_prompt is not None:
        fields.append('system_prompt = ?')
        values.append(system_prompt)

    if not fields:
        return

    sql = 'UPDATE agents SET ' + ', '.join(fields) + ' WHERE id = ? AND user_id = ?'
    values.extend([agent_id, user_id])

    conn = connect()
    cur = conn.cursor()
    cur.execute(sql, tuple(values))
    conn.commit()
    conn.close()


def delete_agent(agent_id: int, user_id: int) -> None:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        'DELETE FROM chat_messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ? AND agent_id = ?)',
        (user_id, agent_id),
    )
    cur.execute('DELETE FROM chats WHERE user_id = ? AND agent_id = ?', (user_id, agent_id))
    cur.execute('DELETE FROM agents WHERE id = ? AND user_id = ?', (agent_id, user_id))
    conn.commit()
    conn.close()
