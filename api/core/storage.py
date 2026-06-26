import sqlite3
import os
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = os.getenv("STORAGE_PATH", "data/keycadence.db")


def get_db_path() -> str:
    return os.getenv("STORAGE_PATH", DB_PATH)


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            user_id TEXT PRIMARY KEY,
            mean REAL NOT NULL,
            std REAL NOT NULL,
            samples_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def save_baseline(user_id: str, mean: float, std: float, samples_count: int) -> None:
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO baselines (user_id, mean, std, samples_count)
        VALUES (?, ?, ?, ?)
    """, (user_id, mean, std, samples_count))
    conn.commit()
    conn.close()


def load_baseline(user_id: str) -> Optional[Tuple[float, float, int]]:
    conn = get_connection()
    row = conn.execute(
        "SELECT mean, std, samples_count FROM baselines WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return row[0], row[1], row[2]
