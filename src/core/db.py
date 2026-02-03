import os
import sqlite3
from pathlib import Path

def get_db_path() -> str:
    return os.getenv("APP_DB_PATH", "data/app.db")

def connect():
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        name TEXT NOT NULL,
        description TEXT,
        model TEXT NOT NULL,
        max_tokens INTEGER NOT NULL,
        temperature REAL NOT NULL,
        system_prompt TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    # Chats: uma conversa por agente (múltiplos chats por agente)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        agent_id INTEGER NOT NULL REFERENCES agents(id),
        title TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    # Migração: se chat_messages antiga (user_id, agent_id) existir, substituir pela nova (chat_id)
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_messages'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(chat_messages)")
        cols = [row[1] for row in cur.fetchall()]
        if "agent_id" in cols:
            cur.execute("DROP TABLE chat_messages")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()
