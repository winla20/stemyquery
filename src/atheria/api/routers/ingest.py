"""POST /api/ingest endpoint."""

from fastapi import APIRouter

from atheria.api.dependencies import get_bm25_index
from atheria.schemas.ingest import IngestRequest, IngestResponse
from atheria.services.ingest_service import IngestService

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    svc = IngestService()
    response = svc.run(req.input_path)
    # Rebuild the cached BM25 index to include newly ingested chunks
    get_bm25_index.cache_clear()
    get_bm25_index()
    return response
