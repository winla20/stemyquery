"""FastAPI application and CLI entry point for Atheria."""

import argparse
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from atheria.api.dependencies import get_bm25_index
from atheria.api.routers import chunks, ingest, papers, query
from atheria.db.connection import get_connection
from atheria.db.migrations import apply_migrations
from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.db.repositories.paper_repo import PaperRepository
from atheria.index.dense_index import SqliteVecAdapter, count_embeddings
from atheria.retrieval.formatter import format_results
from atheria.retrieval.hybrid import hybrid_retrieve
from atheria.schemas.papers import HealthOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: apply schema and warm up the BM25 cache."""
    conn = get_connection()
    apply_migrations(conn)
    conn.close()
    get_bm25_index()  # triggers @lru_cache build
    yield


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Atheria Section Finder",
        version="2.0.0",
        lifespan=lifespan,
    )

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _app.include_router(query.router, prefix="/api")
    _app.include_router(papers.router, prefix="/api")
    _app.include_router(chunks.router, prefix="/api")
    _app.include_router(ingest.router, prefix="/api")

    @_app.get("/api/health", response_model=HealthOut)
    def health():
        conn = get_connection()
        try:
            paper_count = PaperRepository(conn).count()
            chunk_count = ChunkRepository(conn).count()
            vec_count = count_embeddings(conn)
        finally:
            conn.close()
        status = "ok" if chunk_count > 0 else "no_index"
        return HealthOut(
            status=status,
            paper_count=paper_count,
            chunk_count=chunk_count,
            vec_count=vec_count,
        )

    return _app


# Module-level app instance for uvicorn
app = create_app()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point (atheria build / atheria query)."""
    from atheria.index.build_index import build_index, load_state

    parser = argparse.ArgumentParser(description="Atheria Section Finder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build_p = sub.add_parser("build", help="Build index from paper(s)")
    build_p.add_argument("--input", "-i", required=True, help="Path to PMC XML/HTML or dir")

    query_p = sub.add_parser("query", help="Query for relevant sections")
    query_p.add_argument("query", nargs="+", help="Query text")
    query_p.add_argument("--paper", "-p", default=None, help="Filter by paper_id")
    query_p.add_argument("--top", "-n", type=int, default=8, help="Number of results")

    args = parser.parse_args()

    if args.cmd == "build":
        papers_list, chunks_list = build_index(args.input)
        print(f"Indexed {len(papers_list)} paper(s), {len(chunks_list)} chunk(s)")
        return

    if args.cmd == "query":
        query_text = " ".join(args.query)
        conn = get_connection()
        apply_migrations(conn)
        try:
            paper_by_id, chunk_by_id, bm25 = load_state(conn)
        except Exception as e:
            print(
                f"Failed to load index: {e}\nRun 'atheria build -i data/raw/...' first.",
                file=sys.stderr,
            )
            sys.exit(1)

        dense = SqliteVecAdapter(conn)
        results = hybrid_retrieve(
            query_text, bm25, dense, chunk_by_id, paper_by_id,
            top_n=args.top, paper_id=args.paper,
        )
        formatted = format_results(results, paper_by_id)
        conn.close()

        for i, sp in enumerate(formatted, 1):
            print(f"\n--- Result {i} ({sp.confidence}) ---")
            print(f"Paper: {sp.paper_title}")
            if sp.pmid:
                print(f"PMID: {sp.pmid}")
            print(f"Section: {sp.section_path}")
            print(f"Pages: {sp.page_start}-{sp.page_end}")
            for snip in sp.snippets:
                print(f"  > {snip}")


if __name__ == "__main__":
    main()
