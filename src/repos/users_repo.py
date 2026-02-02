from typing import Optional, List, Dict, Any
from .db import connect
from .auth import hash_password

def create_user(email: str, password: str, role: str, active: bool = True) -> int:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, role, active) VALUES (?, ?, ?, ?)",
        (email.lower().strip(), hash_password(password), role, 1 if active else 0),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def list_users() -> List[Dict[str, Any]]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user(user_id: int, email: Optional[str] = None, role: Optional[str] = None, active: Optional[bool] = None):
    fields = []
    values = []
    if email is not None:
        fields.append("email = ?")
        values.append(email.lower().strip())
    if role is not None:
        fields.append("role = ?")
        values.append(role)
    if active is not None:
        fields.append("active = ?")
        values.append(1 if active else 0)

    if not fields:
        return

    fields.append("updated_at = datetime('now')")
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
    values.append(user_id)

    conn = connect()
    cur = conn.cursor()
    cur.execute(sql, tuple(values))
    conn.commit()
    conn.close()

def set_password(user_id: int, new_password: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()