"""FastAPI app and CLI for Section Finder."""

import argparse
import sys
from pathlib import Path

from atheria.config import INDEX_DIR
from atheria.index.build_index import build_index, load_index
from atheria.retrieval.hybrid import hybrid_retrieve
from atheria.retrieval.formatter import format_results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Atheria Section Finder")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # build
    build_p = sub.add_parser("build", help="Build index from paper(s)")
    build_p.add_argument("--input", "-i", required=True, help="Path to PMC XML/HTML or dir")
    build_p.add_argument("--output", "-o", default=str(INDEX_DIR), help="Output index directory")

    # query
    query_p = sub.add_parser("query", help="Query for relevant sections")
    query_p.add_argument("query", nargs="+", help="Query text")
    query_p.add_argument("--index", "-i", default=str(INDEX_DIR), help="Index directory")
    query_p.add_argument("--paper", "-p", default=None, help="Filter by paper_id")
    query_p.add_argument("--top", "-n", type=int, default=8, help="Number of results")

    args = parser.parse_args()

    if args.cmd == "build":
        papers, chunks = build_index(args.input, args.output)
        print(f"Indexed {len(papers)} paper(s), {len(chunks)} chunk(s)")
        return

    if args.cmd == "query":
        query_text = " ".join(args.query)
        try:
            paper_by_id, chunk_by_id, bm25, dense = load_index(args.index)
        except FileNotFoundError:
            print("Index not found. Run 'atheria build -i data/raw/sample_pmc.xml' first.", file=sys.stderr)
            sys.exit(1)

        results = hybrid_retrieve(
            query_text,
            bm25,
            dense,
            chunk_by_id,
            paper_by_id,
            top_n=args.top,
            paper_id=args.paper,
        )
        formatted = format_results(results, paper_by_id)

        for i, sp in enumerate(formatted, 1):
            print(f"\n--- Result {i} ({sp.confidence}) ---")
            print(f"Paper: {sp.paper_title}")
            if sp.pmid:
                print(f"PMID: {sp.pmid}")
            print(f"Section: {sp.section_path}")
            print(f"Pages: {sp.page_start}-{sp.page_end}")
            for snip in sp.snippets:
                print(f"  > {snip}")
        return


if __name__ == "__main__":
    main()


def create_app():
    """Create FastAPI app for programmatic/HTTP use."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Atheria Section Finder", version="0.1.0")

    _index_loaded = False
    _paper_by_id = {}
    _chunk_by_id = {}
    _bm25 = None
    _dense = None

    def ensure_index():
        nonlocal _index_loaded, _paper_by_id, _chunk_by_id, _bm25, _dense
        if not _index_loaded:
            try:
                _paper_by_id, _chunk_by_id, _bm25, _dense = load_index()
                _index_loaded = True
            except FileNotFoundError:
                raise HTTPException(503, "Index not built. Run: atheria build -i data/raw/sample_pmc.xml")

    class QueryRequest(BaseModel):
        query: str
        paper_id: str | None = None
        top_n: int = 8

    class SectionPointerOut(BaseModel):
        paper_title: str
        paper_id: str
        pmid: str | None
        doi: str | None
        section_path: str
        page_start: int
        page_end: int
        snippets: list[str]
        confidence: str
        chunk_id: str

    @app.post("/query")
    def api_query(req: QueryRequest):
        ensure_index()
        results = hybrid_retrieve(
            req.query,
            _bm25,
            _dense,
            _chunk_by_id,
            _paper_by_id,
            top_n=req.top_n,
            paper_id=req.paper_id,
        )
        formatted = format_results(results, _paper_by_id)
        return [
            SectionPointerOut(
                paper_title=sp.paper_title,
                paper_id=sp.paper_id,
                pmid=sp.pmid,
                doi=sp.doi,
                section_path=sp.section_path,
                page_start=sp.page_start,
                page_end=sp.page_end,
                snippets=sp.snippets,
                confidence=sp.confidence,
                chunk_id=sp.chunk_id,
            )
            for sp in formatted
        ]

    return app
