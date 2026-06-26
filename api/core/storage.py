import sqlite3
import os
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = os.getenv("STORAGE_PATH", "data/keycadence.db")


def get_db_path() -> str:
    """Return the database file path from STORAGE_PATH env or default."""
    return os.getenv("STORAGE_PATH", DB_PATH)


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode enabled.

    Creates the parent directory if it does not exist. WAL mode allows
    concurrent reads without blocking each other.

    Returns:
        An open sqlite3.Connection.
    """
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the baselines table if it does not already exist.

    Called once at application startup via the lifespan handler.
    The table stores per-user keystroke baselines (mean, std, sample count).
    """
    conn = get_connection()
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
    conn.close()


def save_baseline(user_id: str, mean: float, std: float, samples_count: int) -> None:
    """Insert or overwrite a user's keystroke baseline.

    Uses INSERT OR REPLACE so re-enrolling a user replaces their previous
    baseline. The connection is managed via context manager to guarantee
    cleanup even on error.

    Args:
        user_id: Unique identifier for the user.
        mean: Mean keystroke timing from the enrollment sample.
        std: Standard deviation of the enrollment sample.
        samples_count: Number of timing intervals in the sample.
    """
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO baselines (user_id, mean, std, samples_count)
            VALUES (?, ?, ?, ?)
        """, (user_id, mean, std, samples_count))
        conn.commit()


def load_baseline(user_id: str) -> Optional[Tuple[float, float, int]]:
    """Retrieve a user's stored keystroke baseline.

    Args:
        user_id: The user to look up.

    Returns:
        Tuple of (mean, std, samples_count) if found, None otherwise.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT mean, std, samples_count FROM baselines WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return row[0], row[1], row[2]


def delete_baseline(user_id: str) -> bool:
    """Delete a user's baseline from the database.

    Used for POPIA data erasure requests.

    Args:
        user_id: The user whose baseline should be removed.

    Returns:
        True if a row was deleted, False if the user did not exist.
    """
    conn = get_connection()
    cursor = conn.execute("DELETE FROM baselines WHERE user_id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
