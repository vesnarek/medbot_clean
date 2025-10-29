import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional

DB_NAME = "sessions.db"


def init_db() -> None:
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                created_at TEXT,
                symptoms TEXT,
                onset TEXT,
                context TEXT,
                analyses TEXT,
                analysis_details TEXT,
                psycho_state TEXT,
                life_events TEXT,
                gpt_reply TEXT
            )
        """)


def save_session(user_id: int, data: dict, gpt_reply: str) -> None:
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO sessions (
                user_id, created_at, symptoms, onset, context, analyses,
                analysis_details, psycho_state, life_events, gpt_reply
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            datetime.utcnow().isoformat(),
            data.get("symptoms"),
            data.get("onset"),
            data.get("context"),
            data.get("analyses"),
            data.get("analysis_details"),
            data.get("psycho_state"),
            data.get("life_events"),
            gpt_reply
        ))


def get_last_sessions(user_id: int, limit: int = 5) -> List[Tuple[int, str, str]]:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute("""
            SELECT id, created_at, gpt_reply
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        return cursor.fetchall()
