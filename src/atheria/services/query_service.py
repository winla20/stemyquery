"""Orchestrates the hybrid retrieval pipeline with injected DB and models."""

import sqlite3

from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.db.repositories.paper_repo import PaperRepository
from atheria.index.bm25_index import BM25Index
from atheria.index.dense_index import SqliteVecAdapter
from atheria.retrieval.formatter import format_results
from atheria.retrieval.hybrid import expand_query, hybrid_retrieve
from atheria.schemas.query import QueryRequest, QueryResponse, SectionPointerOut


class QueryService:
    def __init__(
        self,
        conn: sqlite3.Connection,
        bm25: BM25Index,
    ) -> None:
        self._conn = conn
        self._bm25 = bm25
        self._dense = SqliteVecAdapter(conn)

    def search(self, request: QueryRequest) -> QueryResponse:
        paper_repo = PaperRepository(self._conn)
        chunk_repo = ChunkRepository(self._conn)

        paper_by_id = paper_repo.get_all_as_dict()

        # BM25 + dense retrieval via hybrid_retrieve uses chunk_by_id for hydration.
        # We load all chunks lazily; for large indexes consider loading only candidates.
        chunk_by_id = chunk_repo.get_chunks_by_ids(
            [cid for cid, _ in self._bm25.retrieve(request.query, k=200)]
            + [cid for cid, _ in self._dense.retrieve(request.query, k=200, paper_id=request.paper_id)]
        )

        scored = hybrid_retrieve(
            request.query,
            self._bm25,
            self._dense,
            chunk_by_id,
            paper_by_id,
            top_n=request.top_n,
            paper_id=request.paper_id,
            use_query_expansion=request.use_query_expansion,
        )

        formatted = format_results(scored, paper_by_id)
        query_used = expand_query(request.query) if request.use_query_expansion else request.query

        return QueryResponse(
            results=[
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
                    reranker_score=sp.reranker_score,
                )
                for sp in formatted
            ],
            query_used=query_used,
            total=len(formatted),
        )
