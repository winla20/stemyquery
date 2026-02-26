"""GET /api/papers endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from atheria.api.dependencies import get_db
from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.db.repositories.paper_repo import PaperRepository
from atheria.schemas.papers import ChunkOut, PaperOut

router = APIRouter()


@router.get("/papers", response_model=list[PaperOut])
def list_papers(conn: sqlite3.Connection = Depends(get_db)):
    repo = PaperRepository(conn)
    rows = repo.get_all_with_chunk_counts()
    return [
        PaperOut(
            paper_id=r["paper_id"],
            title=r["title"],
            pmid=r.get("pmid"),
            doi=r.get("doi"),
            source_url=r.get("source_url"),
            chunk_count=r["chunk_count"],
        )
        for r in rows
    ]


@router.get("/papers/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: str, conn: sqlite3.Connection = Depends(get_db)):
    repo = PaperRepository(conn)
    rows = repo.get_all_with_chunk_counts()
    for r in rows:
        if r["paper_id"] == paper_id:
            return PaperOut(
                paper_id=r["paper_id"],
                title=r["title"],
                pmid=r.get("pmid"),
                doi=r.get("doi"),
                source_url=r.get("source_url"),
                chunk_count=r["chunk_count"],
            )
    raise HTTPException(status_code=404, detail="Paper not found")


@router.get("/papers/{paper_id}/chunks", response_model=list[ChunkOut])
def get_paper_chunks(paper_id: str, conn: sqlite3.Connection = Depends(get_db)):
    chunk_repo = ChunkRepository(conn)
    chunks = chunk_repo.get_by_paper(paper_id)
    return [
        ChunkOut(
            chunk_id=c.chunk_id,
            paper_id=c.paper_id,
            chunk_type=c.chunk_type.value,
            section_path=c.section_path,
            page_start=c.page_start,
            page_end=c.page_end,
            text=c.text,
        )
        for c in chunks
    ]
