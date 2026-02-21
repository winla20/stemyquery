"""Paper data model."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Paper:
    """A biomedical paper."""

    paper_id: UUID
    title: str
    pmid: str | None = None
    source_url: str | None = None
    pdf_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        title: str,
        pmid: str | None = None,
        source_url: str | None = None,
        pdf_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "Paper":
        return cls(
            paper_id=uuid4(),
            title=title,
            pmid=pmid,
            source_url=source_url,
            pdf_path=pdf_path,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        return {
            "paper_id": str(self.paper_id),
            "title": self.title,
            "pmid": self.pmid,
            "source_url": self.source_url,
            "pdf_path": self.pdf_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        return cls(
            paper_id=UUID(d["paper_id"]),
            title=d["title"],
            pmid=d.get("pmid"),
            source_url=d.get("source_url"),
            pdf_path=d.get("pdf_path"),
            metadata=d.get("metadata", {}),
        )
