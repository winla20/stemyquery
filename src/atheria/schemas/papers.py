"""Pydantic schemas for papers and chunks endpoints."""

from pydantic import BaseModel


class PaperOut(BaseModel):
    paper_id: str
    title: str
    pmid: str | None
    doi: str | None
    source_url: str | None
    chunk_count: int


class ChunkOut(BaseModel):
    chunk_id: str
    paper_id: str
    chunk_type: str
    section_path: list[str]
    page_start: int
    page_end: int
    text: str


class ChunkContextOut(BaseModel):
    prev: ChunkOut | None
    current: ChunkOut
    next: ChunkOut | None


class HealthOut(BaseModel):
    status: str
    paper_count: int
    chunk_count: int
    vec_count: int
