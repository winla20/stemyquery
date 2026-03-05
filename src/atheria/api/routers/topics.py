"""GET /api/topics endpoints for topic browse and drill-down."""

import json
import sqlite3
from itertools import groupby
from operator import itemgetter

from fastapi import APIRouter, Depends, HTTPException

from atheria.api.dependencies import get_db
from atheria.db.repositories.chunk_repo import ChunkRepository
from atheria.schemas.topics import (
    PaperGroupOut,
    TopicChunkOut,
    TopicDrillDownOut,
    TopicOut,
)

router = APIRouter()


@router.get("/topics", response_model=list[TopicOut])
def list_topics(conn: sqlite3.Connection = Depends(get_db)):
    repo = ChunkRepository(conn)
    rows = repo.get_all_topics()
    return [TopicOut(**r) for r in rows]


@router.get("/topics/{topic}/chunks", response_model=TopicDrillDownOut)
def get_topic_chunks(topic: str, conn: sqlite3.Connection = Depends(get_db)):
    repo = ChunkRepository(conn)
    rows = repo.get_chunks_by_topic(topic)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No chunks found for topic '{topic}'")

    papers: list[PaperGroupOut] = []
    for paper_id, group in groupby(rows, key=itemgetter("paper_id")):
        group_list = list(group)
        first = group_list[0]
        chunks = [
            TopicChunkOut(
                chunk_id=r["chunk_id"],
                paper_id=r["paper_id"],
                paper_title=r["paper_title"],
                chunk_type=r["chunk_type"],
                section_path=json.loads(r["section_path"]) if isinstance(r["section_path"], str) else r["section_path"],
                page_start=r["page_start"],
                page_end=r["page_end"],
                snippet=r["text"][:300],
            )
            for r in group_list
        ]
        papers.append(
            PaperGroupOut(
                paper_id=paper_id,
                paper_title=first["paper_title"],
                pmid=first["pmid"],
                doi=first["doi"],
                chunks=chunks,
            )
        )

    return TopicDrillDownOut(
        topic=topic,
        total_chunks=len(rows),
        papers=papers,
    )
