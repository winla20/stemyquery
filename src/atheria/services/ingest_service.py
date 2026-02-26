"""Orchestrates the parse + chunk + index pipeline."""

from pathlib import Path

from atheria.index.build_index import build_index
from atheria.schemas.ingest import IngestResponse


class IngestService:
    def run(self, input_path: str) -> IngestResponse:
        papers, chunks = build_index(input_path)
        return IngestResponse(
            papers_indexed=len(papers),
            chunks_indexed=len(chunks),
            paper_ids=[str(p.paper_id) for p in papers],
        )
