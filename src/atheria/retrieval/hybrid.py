"""Hybrid retrieval: BM25 + Dense + MedCPT reranker."""

from typing import Any

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

from atheria.config import K_SPARSE, K_DENSE, K_MERGE, TOP_N, MEDCPT_CROSS_ENCODER


# Synonym dict for query expansion (biochem metrics)
SYNONYM_DICT: dict[str, list[str]] = {
    "auroc": ["ROC-AUC", "AUC-ROC", "area under curve"],
    "roc-auc": ["AUROC", "AUC-ROC"],
    "catd": ["calcium transient duration", "CaTD"],
    "calcium transient duration": ["CaTD", "Ca2+ transient"],
    "apd90": ["action potential duration 90", "APD90"],
    "action potential duration": ["APD", "APD90"],
}


def expand_query(query: str) -> str:
    """Add synonyms for known terms to improve recall."""
    qlower = query.lower()
    added: list[str] = []
    for term, syns in SYNONYM_DICT.items():
        if term in qlower:
            for s in syns[:1]:  # Add at most one synonym per term
                if s.lower() not in qlower:
                    added.append(s)
                    break
    if added:
        return query + " " + " ".join(added)
    return query


def hybrid_retrieve(
    query: str,
    bm25_index: Any,
    dense_index: Any,
    chunk_by_id: dict[str, Any],
    paper_by_id: dict[str, Any],
    k_sparse: int = K_SPARSE,
    k_dense: int = K_DENSE,
    top_n: int = TOP_N,
    paper_id: str | None = None,
    use_query_expansion: bool = True,
) -> list[tuple[Any, float]]:
    """
    Run hybrid retrieval: BM25 + Dense merge, then MedCPT rerank.

    Returns list of (chunk, reranker_score) for top_n chunks.
    """
    q = expand_query(query) if use_query_expansion else query

    # Candidate generation
    bm25_hits = bm25_index.retrieve(q, k=k_sparse)
    dense_hits = dense_index.retrieve(query, k=k_dense, paper_id=paper_id)

    # Merge and dedupe by chunk_id
    seen: set[str] = set()
    merged: list[tuple[str, float]] = []
    for cid, score in bm25_hits + dense_hits:
        if cid not in seen and cid in chunk_by_id:
            seen.add(cid)
            merged.append((cid, score))
        if len(merged) >= K_MERGE:
            break

    if not merged:
        return []

    # Get chunk texts for reranker
    chunk_ids = [cid for cid, _ in merged]
    chunks = [chunk_by_id[cid] for cid in chunk_ids if cid in chunk_by_id]
    if not chunks:
        return []

    # Rerank with MedCPT Cross-Encoder
    pairs = [[query, c.text] for c in chunks]
    tokenizer = AutoTokenizer.from_pretrained(MEDCPT_CROSS_ENCODER)
    model = AutoModelForSequenceClassification.from_pretrained(MEDCPT_CROSS_ENCODER)
    model.eval()

    all_scores: list[float] = []
    batch_size = 32
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i : i + batch_size]
        with torch.no_grad():
            encoded = tokenizer(
                batch,
                truncation=True,
                padding=True,
                return_tensors="pt",
                max_length=512,
            )
            logits = model(**encoded).logits.squeeze(dim=1)
            all_scores.extend(logits.cpu().tolist())

    scored = list(zip(chunks, all_scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    # Dedupe by chunk_id (keep first occurrence) so we never return the same chunk twice
    seen_ids: set[str] = set()
    unique: list[tuple[Any, float]] = []
    for c, s in scored:
        cid = getattr(c, "chunk_id", id(c))
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique.append((c, s))
    return unique[:top_n]
