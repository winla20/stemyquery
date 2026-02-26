"""POST /api/query endpoint."""

import sqlite3

from fastapi import APIRouter, Depends

from atheria.api.dependencies import get_bm25_index, get_db
from atheria.index.bm25_index import BM25Index
from atheria.schemas.query import QueryRequest, QueryResponse
from atheria.services.query_service import QueryService

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def search(
    req: QueryRequest,
    conn: sqlite3.Connection = Depends(get_db),
    bm25: BM25Index = Depends(get_bm25_index),
):
    svc = QueryService(conn, bm25)
    return svc.search(req)
