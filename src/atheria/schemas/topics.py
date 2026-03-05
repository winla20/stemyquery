"""Pydantic schemas for topic browse and drill-down."""

from pydantic import BaseModel


class TopicOut(BaseModel):
    topic: str
    chunk_count: int
    paper_count: int


class TopicChunkOut(BaseModel):
    chunk_id: str
    paper_id: str
    paper_title: str
    chunk_type: str
    section_path: list[str]
    page_start: int
    page_end: int
    snippet: str


class PaperGroupOut(BaseModel):
    paper_id: str
    paper_title: str
    pmid: str | None
    doi: str | None
    chunks: list[TopicChunkOut]


class TopicDrillDownOut(BaseModel):
    topic: str
    total_chunks: int
    papers: list[PaperGroupOut]
