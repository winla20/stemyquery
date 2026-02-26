"""SQLite schema migrations."""

import sqlite3

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS papers (
    paper_id    TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    pmid        TEXT,
    doi         TEXT,
    source_url  TEXT,
    pdf_path    TEXT,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    paper_id        TEXT NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    chunk_type      TEXT NOT NULL,
    section_path    TEXT NOT NULL DEFAULT '[]',
    page_start      INTEGER NOT NULL DEFAULT 1,
    page_end        INTEGER NOT NULL DEFAULT 1,
    text            TEXT NOT NULL,
    bm25_fields     TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_chunks_paper_id ON chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(paper_id, page_start);

CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    embedding float[768],
    +paper_id TEXT,
    +chunk_id TEXT
);
"""


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply schema (idempotent — all statements use IF NOT EXISTS)."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
