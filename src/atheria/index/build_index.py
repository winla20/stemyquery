"""Build BM25 + dense index from papers."""

import json
from pathlib import Path

from atheria.config import (
    CHROMA_PATH,
    BM25_PATH,
    CHUNKS_PATH,
    PAPERS_PATH,
    INDEX_DIR,
    RAW_DIR,
)
from atheria.models.paper import Paper
from atheria.models.chunk import Chunk
from atheria.ingest.pmc_parser import parse_pmc, parse_raw_text
from atheria.ingest.chunker import chunk_document
from atheria.index.bm25_index import BM25Index
from atheria.index.dense_index import DenseIndex


def build_index(
    input_path: str | Path,
    output_dir: str | Path | None = None,
) -> tuple[list[Paper], list[Chunk]]:
    """
    Parse paper(s), chunk, and build BM25 + dense index.

    Input can be:
    - Path to PMC XML/HTML file
    - Path to directory of PMC files
    - Path to raw .txt file (fallback)

    Returns (papers, chunks).
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir) if output_dir else INDEX_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    chroma_path = output_dir / "chroma"
    bm25_path = output_dir / "bm25"

    papers: list[Paper] = []
    all_chunks: list[Chunk] = []

    # Collect files to process
    files: list[Path] = []
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = list(input_path.glob("*.xml")) + list(input_path.glob("*.nxml")) + list(input_path.glob("*.html")) + list(input_path.glob("*.htm"))
        if not files:
            files = list(input_path.glob("*.txt"))

    for f in files:
        doc = parse_pmc(f)
        if doc is None:
            doc = parse_raw_text(f)
        if doc is None:
            continue

        metadata = doc.metadata or {}
        paper = Paper.create(
            title=doc.title,
            pmid=metadata.get("pmid"),
            source_url=metadata.get("source_url"),
            metadata=metadata,
        )
        papers.append(paper)
        chunks = chunk_document(doc, paper)
        all_chunks.extend(chunks)

    if not all_chunks:
        return papers, all_chunks

    # Build BM25 index
    bm25 = BM25Index()
    bm25.add_chunks(all_chunks)
    bm25.save(str(bm25_path))

    # Build dense index (reset to overwrite previous)
    dense = DenseIndex(persist_path=str(chroma_path))
    dense.add_chunks(all_chunks, reset=True)

    # Persist chunks and papers for retrieval
    chunks_data = [c.to_dict() for c in all_chunks]
    papers_data = [p.to_dict() for p in papers]
    with open(output_dir / "chunks.json", "w") as fp:
        json.dump(chunks_data, fp, indent=2)
    with open(output_dir / "papers.json", "w") as fp:
        json.dump(papers_data, fp, indent=2)

    return papers, all_chunks


def load_index(output_dir: str | Path | None = None) -> tuple[dict[str, Paper], dict[str, Chunk], BM25Index, DenseIndex]:
    """Load existing index. Returns (paper_by_id, chunk_by_id, bm25, dense)."""
    from atheria.models.chunk import ChunkType

    output_dir = Path(output_dir) if output_dir else INDEX_DIR
    chunks_data = json.loads((output_dir / "chunks.json").read_text())
    papers_data = json.loads((output_dir / "papers.json").read_text())

    papers = {str(p["paper_id"]): Paper.from_dict(p) for p in papers_data}
    chunks = {c["chunk_id"]: Chunk.from_dict(c) for c in chunks_data}

    bm25 = BM25Index()
    bm25.load(str(output_dir / "bm25"))

    dense = DenseIndex(persist_path=str(output_dir / "chroma"))

    return papers, chunks, bm25, dense
