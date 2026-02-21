"""Evaluation script: Recall@5, MRR."""

import json
import sys
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from atheria.config import INDEX_DIR
from atheria.index.build_index import load_index
from atheria.retrieval.hybrid import hybrid_retrieve
from atheria.retrieval.formatter import format_results


def _section_match(retrieved_path: str, correct_path: str) -> bool:
    """Check if retrieved section path matches correct (substring or equality)."""
    if not correct_path or not retrieved_path:
        return False
    # Normalize: collapse arrows/spaces for flexible matching
    def norm(s: str) -> str:
        return " ".join(s.replace("→", " ").replace(">", " ").lower().split())
    r = norm(retrieved_path)
    c = norm(correct_path)
    return c in r or r in c


def evaluate(
    queries_path: str | Path = None,
    index_dir: str | Path = None,
    top_n: int = 5,
) -> dict:
    """
    Run evaluation. Returns dict with Recall@5, MRR, and per-query details.
    """
    queries_path = queries_path or ROOT / "eval" / "queries.json"
    index_dir = index_dir or INDEX_DIR

    with open(queries_path) as f:
        queries = json.load(f)

    paper_by_id, chunk_by_id, bm25, dense = load_index(index_dir)

    recall_at_5 = 0.0
    mrr_sum = 0.0
    n = len(queries)
    details = []

    for q in queries:
        query = q["query"]
        correct_path = q.get("correct_section_path", "")
        correct_chunk_ids = set(q.get("correct_chunk_ids", []))

        results = hybrid_retrieve(
            query,
            bm25,
            dense,
            chunk_by_id,
            paper_by_id,
            top_n=top_n,
            use_query_expansion=True,
        )
        formatted = format_results(results, paper_by_id)

        # Match: either correct_section_path substring match or correct_chunk_ids
        found_rank = None
        for rank, sp in enumerate(formatted[:top_n], 1):
            if correct_chunk_ids and sp.chunk_id in correct_chunk_ids:
                found_rank = rank
                break
            if correct_path and _section_match(sp.section_path, correct_path):
                found_rank = rank
                break

        if found_rank is not None:
            recall_at_5 += 1
            mrr_sum += 1.0 / found_rank

        details.append({
            "query": query,
            "found_rank": found_rank,
            "top_section": formatted[0].section_path if formatted else None,
        })

    return {
        "recall_at_5": recall_at_5 / n if n else 0,
        "mrr": mrr_sum / n if n else 0,
        "n_queries": n,
        "details": details,
    }


def main():
    result = evaluate()
    print("Recall@5:", f"{result['recall_at_5']:.3f}")
    print("MRR:", f"{result['mrr']:.3f}")
    print("N queries:", result["n_queries"])

    # Optionally write details
    out_path = ROOT / "eval" / "eval_results.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Details written to {out_path}")


if __name__ == "__main__":
    main()
