"""Repository for the papers table."""

import json
import sqlite3
from typing import Any

from atheria.models.paper import Paper


class PaperRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert(self, paper: Paper) -> None:
        doi = paper.metadata.get("doi")
        self.conn.execute(
            """INSERT OR REPLACE INTO papers
               (paper_id, title, pmid, doi, source_url, pdf_path, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                str(paper.paper_id),
                paper.title,
                paper.pmid,
                doi,
                paper.source_url,
                paper.pdf_path,
                json.dumps(paper.metadata),
            ],
        )

    def get_by_id(self, paper_id: str) -> Paper | None:
        row = self.conn.execute(
            "SELECT * FROM papers WHERE paper_id = ?", [paper_id]
        ).fetchone()
        return Paper.from_row(row) if row else None

    def get_all(self) -> list[Paper]:
        rows = self.conn.execute("SELECT * FROM papers").fetchall()
        return [Paper.from_row(r) for r in rows]

    def get_all_as_dict(self) -> dict[str, Paper]:
        return {str(p.paper_id): p for p in self.get_all()}

    def get_all_with_chunk_counts(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT p.*, COUNT(c.chunk_id) as chunk_count
               FROM papers p
               LEFT JOIN chunks c ON c.paper_id = p.paper_id
               GROUP BY p.paper_id"""
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["metadata"] = json.loads(d["metadata"])
            result.append(d)
        return result

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
