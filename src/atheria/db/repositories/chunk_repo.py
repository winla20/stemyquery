"""Repository for the chunks table."""

import json
import sqlite3
from types import SimpleNamespace

from atheria.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert(self, chunk: Chunk) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO chunks
               (chunk_id, paper_id, chunk_type, section_path,
                page_start, page_end, text, bm25_fields)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                chunk.chunk_id,
                chunk.paper_id,
                chunk.chunk_type.value,
                json.dumps(chunk.section_path),
                chunk.page_start,
                chunk.page_end,
                chunk.text,
                json.dumps(chunk.bm25_fields),
            ],
        )

    def get_by_id(self, chunk_id: str) -> Chunk | None:
        row = self.conn.execute(
            "SELECT * FROM chunks WHERE chunk_id = ?", [chunk_id]
        ).fetchone()
        return Chunk.from_row(row) if row else None

    def get_by_paper(self, paper_id: str) -> list[Chunk]:
        rows = self.conn.execute(
            "SELECT * FROM chunks WHERE paper_id = ? ORDER BY page_start, chunk_id",
            [paper_id],
        ).fetchall()
        return [Chunk.from_row(r) for r in rows]

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> dict[str, Chunk]:
        if not chunk_ids:
            return {}
        placeholders = ",".join("?" * len(chunk_ids))
        rows = self.conn.execute(
            f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})", chunk_ids
        ).fetchall()
        return {r["chunk_id"]: Chunk.from_row(r) for r in rows}

    def load_all_for_bm25(self) -> list[SimpleNamespace]:
        """Load minimal data needed to rebuild the in-memory BM25 index."""
        rows = self.conn.execute(
            "SELECT chunk_id, bm25_fields FROM chunks"
        ).fetchall()
        result = []
        for row in rows:
            ns = SimpleNamespace()
            ns.chunk_id = row["chunk_id"]
            ns.bm25_fields = json.loads(row["bm25_fields"])
            result.append(ns)
        return result

    def get_context(self, chunk_id: str) -> tuple[Chunk | None, Chunk | None, Chunk | None]:
        """Return (prev, current, next) chunks ordered by page_start within same paper."""
        current = self.get_by_id(chunk_id)
        if current is None:
            return None, None, None

        # Get all chunks for this paper ordered by page then insertion order (chunk_id)
        siblings = self.conn.execute(
            """SELECT chunk_id FROM chunks
               WHERE paper_id = ?
               ORDER BY page_start, chunk_id""",
            [current.paper_id],
        ).fetchall()

        ids = [r["chunk_id"] for r in siblings]
        try:
            idx = ids.index(chunk_id)
        except ValueError:
            return None, current, None

        prev_id = ids[idx - 1] if idx > 0 else None
        next_id = ids[idx + 1] if idx < len(ids) - 1 else None

        prev = self.get_by_id(prev_id) if prev_id else None
        nxt = self.get_by_id(next_id) if next_id else None
        return prev, current, nxt

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
