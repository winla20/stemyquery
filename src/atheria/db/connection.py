"""SQLite connection factory with optional sqlite-vec extension loading."""

import sqlite3
import logging
from typing import Final

try:
    import sqlite_vec
except Exception:  # pragma: no cover - optional dependency at runtime
    sqlite_vec = None  # type: ignore[assignment]

from atheria.config import DB_PATH

_PRAGMA_MODULE_LIST: Final[str] = "PRAGMA module_list"
logger = logging.getLogger(__name__)


def has_vec0_module(conn: sqlite3.Connection) -> bool:
    """Return True if the current connection can create vec0 virtual tables."""
    try:
        rows = conn.execute(_PRAGMA_MODULE_LIST).fetchall()
    except sqlite3.DatabaseError:
        return False
    return any(row[0] == "vec0" for row in rows)


def get_connection() -> sqlite3.Connection:
    """Open a WAL-mode sqlite3 connection and load sqlite-vec when possible."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    if sqlite_vec is not None and hasattr(conn, "enable_load_extension") and hasattr(conn, "load_extension"):
        try:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
        except Exception:
            logger.warning("Failed to load sqlite-vec extension; continuing with BM25-only mode.")
        finally:
            conn.enable_load_extension(False)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
