"""Pydantic schemas for the query endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    paper_id: str | None = None
    top_n: int = Field(default=8, ge=1, le=20)
    use_query_expansion: bool = True


class SectionPointerOut(BaseModel):
    paper_title: str
    paper_id: str
    pmid: str | None
    doi: str | None
    section_path: str
    page_start: int
    page_end: int
    snippets: list[str]
    confidence: Literal["high", "med", "low"]
    chunk_id: str
    reranker_score: float


class QueryResponse(BaseModel):
    results: list[SectionPointerOut]
    query_used: str
    total: int
