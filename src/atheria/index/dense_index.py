"""Dense index using MedCPT Article Encoder + ChromaDB."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from transformers import AutoModel, AutoTokenizer
import torch


class DenseIndex:
    """MedCPT embeddings stored in ChromaDB."""

    def __init__(
        self,
        article_model: str = "ncbi/MedCPT-Article-Encoder",
        query_model: str = "ncbi/MedCPT-Query-Encoder",
        persist_path: str | Path | None = None,
    ) -> None:
        self.article_model = article_model
        self.query_model = query_model
        self._article_tokenizer: AutoTokenizer | None = None
        self._article_model: AutoModel | None = None
        self._query_tokenizer: AutoTokenizer | None = None
        self._query_model: AutoModel | None = None
        self._chroma: chromadb.PersistentClient | chromadb.EphemeralClient | None = None
        self._collection_name = "atheria_chunks"
        self._persist_path = str(persist_path) if persist_path else None

    def _ensure_article_model(self) -> None:
        if self._article_tokenizer is None:
            self._article_tokenizer = AutoTokenizer.from_pretrained(self.article_model)
            self._article_model = AutoModel.from_pretrained(self.article_model)
            self._article_model.eval()

    def _ensure_query_model(self) -> None:
        if self._query_tokenizer is None:
            self._query_tokenizer = AutoTokenizer.from_pretrained(self.query_model)
            self._query_model = AutoModel.from_pretrained(self.query_model)
            self._query_model.eval()

    def _ensure_chroma(self) -> chromadb.Collection:
        if self._chroma is None:
            if self._persist_path:
                Path(self._persist_path).mkdir(parents=True, exist_ok=True)
                self._chroma = chromadb.PersistentClient(
                    path=self._persist_path,
                    settings=Settings(anonymized_telemetry=False),
                )
            else:
                self._chroma = chromadb.EphemeralClient()
        return self._chroma.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _encode_articles(self, articles: list[list[str]], batch_size: int = 32) -> list[list[float]]:
        """Encode articles as [[title, abstract], ...]. Returns list of 768-dim vectors."""
        self._ensure_article_model()
        all_embeds: list[list[float]] = []
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            with torch.no_grad():
                encoded = self._article_tokenizer(
                    batch,
                    truncation=True,
                    padding=True,
                    return_tensors="pt",
                    max_length=512,
                )
                outputs = self._article_model(**encoded)
                embeds = outputs.last_hidden_state[:, 0, :].cpu().tolist()
            all_embeds.extend(embeds)
        return all_embeds

    def _encode_query(self, query: str) -> list[float]:
        """Encode query using MedCPT Query Encoder (shared embedding space with Article Encoder)."""
        self._ensure_query_model()
        with torch.no_grad():
            encoded = self._query_tokenizer(
                [query],
                truncation=True,
                padding=True,
                return_tensors="pt",
                max_length=64,
            )
            outputs = self._query_model(**encoded)
            return outputs.last_hidden_state[:, 0, :].cpu().tolist()[0]

    def add_chunks(self, chunks: list, batch_size: int = 32, reset: bool = False) -> None:
        """Add chunks to ChromaDB. Each chunk: section_path, text, chunk_id, paper_id, etc.
        If reset=True, delete existing collection before adding."""
        if reset:
            self._ensure_chroma()
            try:
                self._chroma.delete_collection(self._collection_name)
            except Exception:
                pass
        if not chunks:
            return
        articles = []
        ids = []
        metadatas: list[dict[str, Any]] = []
        for c in chunks:
            section_str = " → ".join(getattr(c, "section_path", []) or [])
            # MedCPT Article Encoder expects [title, abstract]
            articles.append([section_str or "Section", c.text])
            ids.append(c.chunk_id)
            metadatas.append({
                "chunk_id": c.chunk_id,
                "paper_id": str(getattr(c, "paper_id", "")),
                "section_path": " → ".join(getattr(c, "section_path", []) or []),
                "page_start": str(getattr(c, "page_start", 1)),
                "chunk_type": getattr(c, "chunk_type", "").value if hasattr(getattr(c, "chunk_type", ""), "value") else str(getattr(c, "chunk_type", "")),
            })
        embeds = self._encode_articles(articles, batch_size)
        coll = self._ensure_chroma()
        coll.add(ids=ids, embeddings=embeds, metadatas=metadatas)

    def retrieve(self, query: str, k: int = 50, paper_id: str | None = None) -> list[tuple[str, float]]:
        """Return top-k (chunk_id, similarity_score). Higher = more similar."""
        coll = self._ensure_chroma()
        n = coll.count()
        if n == 0:
            return []
        qvec = self._encode_query(query)
        where = {"paper_id": paper_id} if paper_id else None
        results = coll.query(
            query_embeddings=[qvec],
            n_results=min(k, n),
            where=where,
        )
        if not results or not results["ids"] or not results["ids"][0]:
            return []
        ids = results["ids"][0]
        # ChromaDB returns distances (lower = more similar for L2); for cosine it returns 1 - cosine_sim
        dists = results["distances"][0] if results.get("distances") else [0.0] * len(ids)
        # Convert distance to similarity (for cosine: sim = 1 - dist)
        scores = [(cid, 1.0 - d) for cid, d in zip(ids, dists)]
        return scores

    def get_chroma_path(self) -> str | None:
        return self._persist_path
