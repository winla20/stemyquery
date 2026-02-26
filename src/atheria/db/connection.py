"""SQLite connection factory with sqlite-vec extension loaded."""

import sqlite3

import sqlite_vec

from atheria.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a WAL-mode sqlite3 connection with sqlite-vec loaded."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
