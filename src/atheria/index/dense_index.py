"""Dense retrieval using MedCPT embeddings stored in SQLite via sqlite-vec."""

import sqlite3
from typing import Any

import torch
from transformers import AutoModel, AutoTokenizer

import sqlite_vec

from atheria.config import MEDCPT_ARTICLE_ENCODER, MEDCPT_QUERY_ENCODER

# Module-level lazy model state
_article_tokenizer: AutoTokenizer | None = None
_article_model: AutoModel | None = None
_query_tokenizer: AutoTokenizer | None = None
_query_model: AutoModel | None = None


def _ensure_article_model() -> None:
    global _article_tokenizer, _article_model
    if _article_tokenizer is None:
        _article_tokenizer = AutoTokenizer.from_pretrained(MEDCPT_ARTICLE_ENCODER)
        _article_model = AutoModel.from_pretrained(MEDCPT_ARTICLE_ENCODER)
        _article_model.eval()


def _ensure_query_model() -> None:
    global _query_tokenizer, _query_model
    if _query_tokenizer is None:
        _query_tokenizer = AutoTokenizer.from_pretrained(MEDCPT_QUERY_ENCODER)
        _query_model = AutoModel.from_pretrained(MEDCPT_QUERY_ENCODER)
        _query_model.eval()


def encode_articles(articles: list[list[str]], batch_size: int = 32) -> list[list[float]]:
    """Encode [[section, text], ...] pairs. Returns list of 768-dim vectors."""
    _ensure_article_model()
    all_embeds: list[list[float]] = []
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        with torch.no_grad():
            encoded = _article_tokenizer(
                batch,
                truncation=True,
                padding=True,
                return_tensors="pt",
                max_length=512,
            )
            outputs = _article_model(**encoded)
            embeds = outputs.last_hidden_state[:, 0, :].cpu().tolist()
        all_embeds.extend(embeds)
    return all_embeds


def encode_query(query: str) -> list[float]:
    """Encode a single query string to a 768-dim vector."""
    _ensure_query_model()
    with torch.no_grad():
        encoded = _query_tokenizer(
            [query],
            truncation=True,
            padding=True,
            return_tensors="pt",
            max_length=64,
        )
        outputs = _query_model(**encoded)
        return outputs.last_hidden_state[:, 0, :].cpu().tolist()[0]


def store_embeddings(
    conn: sqlite3.Connection,
    chunks: list,
    embeddings: list[list[float]],
) -> None:
    """Insert chunk embeddings into the vec_chunks virtual table.

    Each row in vec_chunks stores: embedding, +paper_id, +chunk_id.
    The +paper_id and +chunk_id are auxiliary (non-indexed) columns used
    to map KNN results back to chunks.
    """
    for chunk, embedding in zip(chunks, embeddings):
        blob = sqlite_vec.serialize_float32(embedding)
        conn.execute(
            "INSERT INTO vec_chunks(embedding, paper_id, chunk_id) VALUES (?, ?, ?)",
            [blob, str(chunk.paper_id), chunk.chunk_id],
        )


def clear_embeddings(conn: sqlite3.Connection) -> None:
    """Remove all rows from the vec_chunks table (for full re-index)."""
    conn.execute("DELETE FROM vec_chunks")


def retrieve_dense(
    conn: sqlite3.Connection,
    query_embedding: list[float],
    k: int = 50,
    paper_id: str | None = None,
) -> list[tuple[str, float]]:
    """Return top-k (chunk_id, similarity) using sqlite-vec KNN.

    Uses L2 distance; similarity = 1 / (1 + distance) to produce a
    descending score comparable to cosine similarity rankings.
    """
    blob = sqlite_vec.serialize_float32(query_embedding)

    if paper_id:
        sql = """
            SELECT chunk_id, distance
            FROM vec_chunks
            WHERE embedding MATCH ? AND paper_id = ?
            ORDER BY distance
            LIMIT ?
        """
        rows = conn.execute(sql, [blob, paper_id, k]).fetchall()
    else:
        sql = """
            SELECT chunk_id, distance
            FROM vec_chunks
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
        """
        rows = conn.execute(sql, [blob, k]).fetchall()

    return [(row["chunk_id"], 1.0 / (1.0 + row["distance"])) for row in rows]


def count_embeddings(conn: sqlite3.Connection) -> int:
    """Return number of stored embeddings."""
    return conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]


# ---------------------------------------------------------------------------
# Adapter: presents the same .retrieve() interface expected by hybrid.py
# ---------------------------------------------------------------------------

class SqliteVecAdapter:
    """Wraps sqlite-vec retrieve_dense() behind the DenseIndex-style interface
    expected by hybrid_retrieve() so that hybrid.py needs zero changes."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def retrieve(self, query: str, k: int = 50, paper_id: str | None = None) -> list[tuple[str, float]]:
        vec = encode_query(query)
        return retrieve_dense(self._conn, vec, k, paper_id)
