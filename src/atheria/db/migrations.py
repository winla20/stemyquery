"""SQLite schema migrations."""

import sqlite3
import logging

from atheria.db.connection import has_vec0_module

logger = logging.getLogger(__name__)

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

"""

_VEC_SCHEMA_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    embedding float[768],
    +paper_id TEXT,
    +chunk_id TEXT
);
"""


_DEDUP_SQL = """
DELETE FROM papers WHERE rowid NOT IN (
    SELECT MIN(rowid) FROM papers GROUP BY LOWER(TRIM(title))
);
"""

# Backfill doi column from metadata JSON for papers indexed before DOI extraction was added
_BACKFILL_DOI_SQL = """
UPDATE papers
SET doi = JSON_EXTRACT(metadata, '$.doi')
WHERE doi IS NULL AND JSON_EXTRACT(metadata, '$.doi') IS NOT NULL;
"""

# Remove papers that were incorrectly indexed (raw PDF binary or known watermark titles)
_BAD_PDF_CLEANUP_SQL = """
DELETE FROM papers WHERE title LIKE '%PDF-%'
    OR LOWER(TRIM(title)) = 'hhs public access'
    OR LOWER(TRIM(title)) = 'author manuscript'
    OR LOWER(TRIM(title)) = '';
"""


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply schema (idempotent — all statements use IF NOT EXISTS)."""
    conn.executescript(SCHEMA_SQL)
    if has_vec0_module(conn):
        conn.executescript(_VEC_SCHEMA_SQL)
    else:
        logger.warning("sqlite-vec unavailable: skipping vec_chunks virtual table migration.")
    conn.executescript(_BAD_PDF_CLEANUP_SQL)
    conn.executescript(_DEDUP_SQL)
    conn.executescript(_BACKFILL_DOI_SQL)
    conn.commit()
