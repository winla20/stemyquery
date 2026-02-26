"""Pydantic schemas for the ingest endpoint."""

from pydantic import BaseModel


class IngestRequest(BaseModel):
    input_path: str


class IngestResponse(BaseModel):
    papers_indexed: int
    chunks_indexed: int
    paper_ids: list[str]
