"""Evidence-first result formatting."""

from dataclasses import dataclass


@dataclass
class SectionPointer:
    """A single section pointer in the formatted output."""

    paper_title: str
    paper_id: str
    pmid: str | None
    doi: str | None
    section_path: str
    page_start: int
    page_end: int
    snippets: list[str]
    confidence: str  # high, med, low
    chunk_id: str
    reranker_score: float


def _extract_snippets(text: str, max_snippets: int = 3, max_len: int = 200) -> list[str]:
    """Extract 1-3 short snippets from chunk text (best sentences)."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return [text[:max_len] + "..." if len(text) > max_len else text]
    result: list[str] = []
    for s in sentences[:max_snippets]:
        if len(s) > max_len:
            s = s[:max_len] + "..."
        result.append(s + ".")
    return result if result else [text[:max_len]]


def _confidence_from_scores(scores: list[float], idx: int) -> str:
    """Assign confidence based on reranker score gap."""
    if not scores or idx >= len(scores):
        return "low"
    s = scores[idx]
    if idx == 0 and len(scores) > 1:
        gap = s - scores[1]
        if gap > 2.0:
            return "high"
        if gap > 0.5:
            return "med"
    elif idx == 0:
        return "high"
    median = scores[len(scores) // 2] if scores else 0
    if s >= median + 1.0:
        return "med"
    return "low"


def format_results(
    scored_chunks: list[tuple],
    paper_by_id: dict,
) -> list[SectionPointer]:
    """
    Format ranked (chunk, score) pairs into SectionPointer objects.

    scored_chunks: list of (chunk, reranker_score)
    paper_by_id: dict mapping paper_id -> Paper
    """
    scores = [sc for _, sc in scored_chunks]
    results: list[SectionPointer] = []
    for idx, (chunk, score) in enumerate(scored_chunks):
        paper = paper_by_id.get(str(chunk.paper_id))
        title = paper.title if paper else "Unknown"
        pmid = paper.pmid if paper else None
        doi = paper.metadata.get("doi") if paper and paper.metadata else None
        snippets = _extract_snippets(chunk.text)
        section_path = chunk.get_section_path_str()
        confidence = _confidence_from_scores(scores, idx)
        results.append(
            SectionPointer(
                paper_title=title,
                paper_id=str(chunk.paper_id),
                pmid=pmid,
                doi=doi,
                section_path=section_path,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                snippets=snippets,
                confidence=confidence,
                chunk_id=chunk.chunk_id,
                reranker_score=float(score),
            )
        )
    return results
