"""Chunk data model."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ChunkType(str, Enum):
    PARAGRAPH = "paragraph"
    TABLE = "table"
    CAPTION = "caption"
    FIGURE_CAPTION = "figure_caption"


@dataclass
class Chunk:
    """A chunk of text from a paper (paragraph, table, caption, etc.)."""

    chunk_id: str
    paper_id: str
    chunk_type: ChunkType
    section_path: list[str]
    page_start: int
    page_end: int
    text: str
    bm25_fields: list[str] = field(default_factory=list)
    dense_vector: list[float] | None = None

    @classmethod
    def create(
        cls,
        paper_id: str,
        chunk_type: ChunkType,
        section_path: list[str],
        page_start: int,
        page_end: int,
        text: str,
    ) -> "Chunk":
        chunk_id = str(uuid4())
        bm25_fields = _build_bm25_fields(section_path, text)
        return cls(
            chunk_id=chunk_id,
            paper_id=paper_id,
            chunk_type=chunk_type,
            section_path=section_path,
            page_start=page_start,
            page_end=page_end,
            text=text,
            bm25_fields=bm25_fields,
        )

    def get_section_path_str(self) -> str:
        return " → ".join(self.section_path) if self.section_path else ""

    def get_full_text_for_indexing(self) -> str:
        """Text with section context for indexing."""
        if self.section_path:
            prefix = "Section: " + " > ".join(self.section_path) + " "
            return prefix + self.text
        return self.text

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "chunk_type": self.chunk_type.value,
            "section_path": self.section_path,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "text": self.text,
            "bm25_fields": self.bm25_fields,
            "dense_vector": self.dense_vector,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(
            chunk_id=d["chunk_id"],
            paper_id=d["paper_id"],
            chunk_type=ChunkType(d["chunk_type"]),
            section_path=d["section_path"],
            page_start=d["page_start"],
            page_end=d["page_end"],
            text=d["text"],
            bm25_fields=d.get("bm25_fields", []),
            dense_vector=d.get("dense_vector"),
        )


# Terms to boost in BM25 (heading-like keywords for biochem metrics)
HEADING_BOOST_TERMS = {
    "assessment",
    "electrophysiology",
    "contractile",
    "maturity",
    "structural",
    "gene expression",
    "metrics",
    "measurement",
    "evaluation",
    "methods",
    "results",
}


def _build_bm25_fields(section_path: list[str], text: str) -> list[str]:
    """Build tokenized fields for BM25 with heading boost (repeat key terms)."""
    parts: list[str] = []
    if section_path:
        parts.append(" ".join(section_path))
    parts.append(text)
    combined = " ".join(parts)
    tokens = combined.lower().split()
    # Add extra copies of heading-like terms for boosting
    for t in tokens:
        if t in HEADING_BOOST_TERMS:
            parts.append(t)
    return parts
