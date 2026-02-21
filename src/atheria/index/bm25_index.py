"""BM25 sparse index with heading boost."""

from pathlib import Path

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenization, lowercase."""
    return text.lower().split()


class BM25Index:
    """BM25 index with chunk_id mapping."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._tokenized_corpus: list[list[str]] = []
        self._chunk_ids: list[str] = []

    def add_chunks(self, chunks: list) -> None:
        """Add chunks; each chunk must have chunk_id and bm25_fields."""
        for chunk in chunks:
            # Combine all bm25_fields into one document for BM25
            combined = " ".join(getattr(chunk, "bm25_fields", [chunk.text]))
            tokens = _tokenize(combined)
            self._tokenized_corpus.append(tokens)
            self._chunk_ids.append(chunk.chunk_id)
        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)

    def retrieve(self, query: str, k: int = 50) -> list[tuple[str, float]]:
        """Return top-k (chunk_id, score) pairs."""
        if not self._bm25:
            return []
        tokenized_query = _tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)
        # Sort by score descending
        indexed = list(zip(self._chunk_ids, scores.tolist()))
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[:k]

    def save(self, path: str | Path) -> None:
        """Persist index to directory (pickle corpus + mapping)."""
        import json
        import pickle

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "corpus.pkl", "wb") as f:
            pickle.dump(self._tokenized_corpus, f)
        with open(path / "chunk_ids.json", "w") as f:
            json.dump(self._chunk_ids, f)

    def load(self, path: str | Path) -> None:
        """Load index from directory."""
        import json
        import pickle

        path = Path(path)
        with open(path / "corpus.pkl", "rb") as f:
            self._tokenized_corpus = pickle.load(f)
        with open(path / "chunk_ids.json") as f:
            self._chunk_ids = json.load(f)
        if self._tokenized_corpus:
            self._bm25 = BM25Okapi(self._tokenized_corpus)
