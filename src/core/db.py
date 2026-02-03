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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        agent_id INTEGER NOT NULL REFERENCES agents(id),
        title TEXT NOT NULL,
        previous_response_id TEXT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # Migracao: se chat_messages antiga (user_id, agent_id) existir, substituir pela nova (chat_id)
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_messages'"
    )
    if cur.fetchone():
        cur.execute("PRAGMA table_info(chat_messages)")
        cols = [row[1] for row in cur.fetchall()]
        if "agent_id" in cols or "user_id" in cols:
            cur.execute("DROP TABLE chat_messages")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tokens INTEGER NOT NULL DEFAULT 0,
        tokens INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # Migracao em chat_messages (tokens)
    cur.execute('PRAGMA table_info(chat_messages)')
    msg_cols = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cur.fetchall()]
    if 'tokens' not in msg_cols:
        cur.execute('ALTER TABLE chat_messages ADD COLUMN tokens INTEGER NOT NULL DEFAULT 0')

    # Migracoes em agents
    cur.execute("PRAGMA table_info(agents)")
    agent_cols = [
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in cur.fetchall()
    ]
    if "description" not in agent_cols:
        cur.execute("ALTER TABLE agents ADD COLUMN description TEXT")
    if "max_tokens" not in agent_cols:
        cur.execute(
            "ALTER TABLE agents ADD COLUMN max_tokens INTEGER NOT NULL DEFAULT 1024"
        )
    if "temperature" not in agent_cols:
        cur.execute(
            "ALTER TABLE agents ADD COLUMN temperature REAL NOT NULL DEFAULT 0.7"
        )
    if "system_prompt" not in agent_cols:
        cur.execute("ALTER TABLE agents ADD COLUMN system_prompt TEXT")
        if "instructions" in agent_cols:
            cur.execute(
                'UPDATE agents SET system_prompt = instructions WHERE system_prompt IS NULL OR system_prompt = ""'
            )
    if "created_at" not in agent_cols:
        cur.execute(
            "ALTER TABLE agents ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        )

    # Migracao em chats
    cur.execute('PRAGMA table_info(chats)')
    chat_cols = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cur.fetchall()]
    if 'previous_response_id' not in chat_cols:
        cur.execute('ALTER TABLE chats ADD COLUMN previous_response_id TEXT')
    if 'updated_at' not in chat_cols:
        cur.execute("ALTER TABLE chats ADD COLUMN updated_at TEXT NOT NULL DEFAULT (datetime('now'))")
    cur.execute("PRAGMA table_info(chats)")
    chat_cols = [
        row["name"] if isinstance(row, sqlite3.Row) else row[1]
        for row in cur.fetchall()
    ]
    if "previous_response_id" not in chat_cols:
        cur.execute("ALTER TABLE chats ADD COLUMN previous_response_id TEXT")

    conn.commit()
    conn.close()
