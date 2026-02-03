# src/core/db.py
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

    # ... (Tabelas users, agents, chats mantidas iguais) ...
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
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # 1. Cria a tabela se não existir (Adicionei a coluna TOKENS)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        tokens INTEGER DEFAULT 0,  -- <--- NOVA COLUNA NECESSÁRIA
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """)

    # 2. Migração de segurança: Se a tabela já existia sem a coluna tokens, adiciona ela agora.
    cur.execute("PRAGMA table_info(chat_messages)")
    columns = [row[1] for row in cur.fetchall()]
    if "tokens" not in columns:
        cur.execute("ALTER TABLE chat_messages ADD COLUMN tokens INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
