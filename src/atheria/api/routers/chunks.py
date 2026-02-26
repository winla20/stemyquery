"""GET /api/chunks endpoints."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from atheria.api.dependencies import get_db
from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.schemas.papers import ChunkContextOut, ChunkOut

router = APIRouter()


def _chunk_to_out(chunk) -> ChunkOut:
    return ChunkOut(
        chunk_id=chunk.chunk_id,
        paper_id=chunk.paper_id,
        chunk_type=chunk.chunk_type.value,
        section_path=chunk.section_path,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        text=chunk.text,
    )


@router.get("/chunks/{chunk_id}", response_model=ChunkOut)
def get_chunk(chunk_id: str, conn: sqlite3.Connection = Depends(get_db)):
    repo = ChunkRepository(conn)
    chunk = repo.get_by_id(chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return _chunk_to_out(chunk)


@router.get("/chunks/{chunk_id}/context", response_model=ChunkContextOut)
def get_chunk_context(chunk_id: str, conn: sqlite3.Connection = Depends(get_db)):
    repo = ChunkRepository(conn)
    prev, current, nxt = repo.get_context(chunk_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return ChunkContextOut(
        prev=_chunk_to_out(prev) if prev else None,
        current=_chunk_to_out(current),
        next=_chunk_to_out(nxt) if nxt else None,
    )
