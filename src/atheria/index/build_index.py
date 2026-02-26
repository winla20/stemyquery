"""Build BM25 + dense index from papers, persisting everything to SQLite."""

from pathlib import Path

from atheria.config import RAW_DIR
from atheria.db.connection import get_connection
from atheria.db.migrations import apply_migrations
from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.db.repositories.paper_repo import PaperRepository
from atheria.index.bm25_index import BM25Index
from atheria.index.dense_index import encode_articles, store_embeddings, clear_embeddings
from atheria.ingest.chunker import chunk_document
from atheria.ingest.pmc_parser import parse_pmc, parse_raw_text
from atheria.models.chunk import Chunk
from atheria.models.paper import Paper


def build_index(
    input_path: str | Path,
) -> tuple[list[Paper], list[Chunk]]:
    """Parse paper(s), chunk, and build BM25 + dense index in SQLite.

    Input can be:
    - Path to a PMC XML/HTML file
    - Path to a directory of PMC files
    - Path to a raw .txt fallback file
    """
    input_path = Path(input_path)

    # Collect files to process
    files: list[Path] = []
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = (
            list(input_path.glob("*.xml"))
            + list(input_path.glob("*.nxml"))
            + list(input_path.glob("*.html"))
            + list(input_path.glob("*.htm"))
        )
        if not files:
            files = list(input_path.glob("*.txt"))

    papers: list[Paper] = []
    all_chunks: list[Chunk] = []

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

    conn = get_connection()
    apply_migrations(conn)

    paper_repo = PaperRepository(conn)
    chunk_repo = ChunkRepository(conn)

    # Write papers and chunks to DB
    for paper in papers:
        paper_repo.insert(paper)
    for chunk in all_chunks:
        chunk_repo.insert(chunk)

    # Build and encode embeddings
    articles = [
        [" → ".join(c.section_path) or "Section", c.text]
        for c in all_chunks
    ]
    print(f"Encoding {len(all_chunks)} chunks with MedCPT Article Encoder...")
    embeddings = encode_articles(articles, batch_size=32)

    # Store in sqlite-vec (clear existing for a fresh index)
    clear_embeddings(conn)
    store_embeddings(conn, all_chunks, embeddings)

    conn.commit()
    conn.close()

    print(f"Indexed {len(papers)} paper(s), {len(all_chunks)} chunk(s).")
    return papers, all_chunks


def load_state(
    conn=None,
) -> tuple[dict[str, Paper], dict[str, Chunk], BM25Index]:
    """Load papers, chunks, and rebuild the in-memory BM25 index from SQLite.

    Returns (paper_by_id, chunk_by_id, bm25).
    Dense retrieval is now a DB query — use SqliteVecAdapter from dense_index.
    """
    if conn is None:
        conn = get_connection()

    paper_repo = PaperRepository(conn)
    chunk_repo = ChunkRepository(conn)

    papers = paper_repo.get_all_as_dict()
    all_chunks = chunk_repo.load_all_for_bm25()

    # Rebuild full Chunk objects for retrieval hydration
    chunk_rows = conn.execute("SELECT * FROM chunks").fetchall()
    chunks = {r["chunk_id"]: Chunk.from_row(r) for r in chunk_rows}

    bm25 = BM25Index()
    bm25.add_chunks(all_chunks)

    return papers, chunks, bm25
