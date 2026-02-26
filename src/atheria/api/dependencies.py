"""FastAPI dependency providers."""

import json
import sqlite3
from functools import lru_cache
from types import SimpleNamespace
from typing import Generator

from atheria.db.connection import get_connection
from atheria.index.bm25_index import BM25Index


@lru_cache(maxsize=1)
def get_bm25_index() -> BM25Index:
    """Build the in-memory BM25 index from bm25_fields stored in the chunks table.
    Cached for the lifetime of the process; call get_bm25_index.cache_clear()
    after ingest to trigger a rebuild on next access.
    """
    conn = get_connection()
    try:
        rows = conn.execute("SELECT chunk_id, bm25_fields FROM chunks").fetchall()
    finally:
        conn.close()

    bm25 = BM25Index()
    pseudo_chunks = []
    for row in rows:
        ns = SimpleNamespace()
        ns.chunk_id = row["chunk_id"]
        ns.bm25_fields = json.loads(row["bm25_fields"])
        pseudo_chunks.append(ns)
    bm25.add_chunks(pseudo_chunks)
    return bm25


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a per-request SQLite connection, closed on teardown."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
