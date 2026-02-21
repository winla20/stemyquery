# Roles of Each Encoder (and Sparse Retriever)

Brief explanations of how each retrieval component is used in Atheria.

---

## BM25 (sparse retriever)

**Role:** Fast keyword-style matching.  
BM25 is not a neural encoder; it scores text by how often query words appear in each chunk (with standard weighting). It’s good at finding exact terms (e.g. “APD90”, “CaTD”) and synonyms we add via query expansion. It runs first to get a pool of candidates and is merged with dense results so we don’t miss keyword-relevant sections.

---

## MedCPT Article Encoder

**Role:** Turn each paper chunk into a fixed-size vector for similarity search.  
The Article Encoder takes a chunk (represented as a short “title + text” pair, as MedCPT expects) and outputs a 768-dimensional vector. These vectors are stored in ChromaDB. They live in the same space as the Query Encoder so we can compare “how close” a chunk is to a query by vector similarity (cosine distance).

---

## MedCPT Query Encoder

**Role:** Turn the user’s question into the same 768-d space as the articles.  
The Query Encoder encodes the search query into one vector. That vector is compared to all stored article vectors in ChromaDB to get the top-k most similar chunks. It’s trained (with the Article Encoder) so that semantically similar questions and passages sit close together, which improves recall for paraphrases and related wording.

---

## MedCPT Cross-Encoder (reranker)

**Role:** Precisely score (query, chunk) pairs to pick the best results.  
The Cross-Encoder is not used to build the index; it runs at query time. It takes the full query and each candidate chunk text together and outputs a single relevance score. We use it to rerank the merged BM25 + dense candidates and return only the top-N. It’s more accurate than cosine similarity alone because it can model direct query–passage interaction, at the cost of more compute per pair.

---

## Merging BM25 + Dense Candidates

The system does **not** combine BM25 and dense scores into one number (they’re on different scales). Instead it uses **interleaved merge with deduplication**:

1. **Get two ranked lists**
   - BM25 returns up to **K_SPARSE** (default 50) `(chunk_id, score)` pairs, ordered by BM25 score.
   - Dense returns up to **K_DENSE** (default 50) `(chunk_id, score)` pairs, ordered by similarity (e.g. cosine).

2. **Concatenate in a fixed order**
   - The combined list is: **all BM25 hits first** (in BM25 order), then **all dense hits** (in dense order). So the iteration order is: BM25 #1, BM25 #2, … BM25 #50, then Dense #1, Dense #2, … Dense #50.

3. **Deduplicate by chunk_id**
   - Walk this combined list from the start. For each `(chunk_id, score)`:
     - If that `chunk_id` has **not** been seen yet and exists in `chunk_by_id`, append it to the **merged** list (we keep the score from whichever list it came from, but the merged list is only used to pass chunk IDs to the reranker; scores are not compared across BM25 vs dense).
     - If the chunk was already seen, skip it (first occurrence wins).
   - Stop when the merged list has **K_MERGE** (default 100) entries, or when we’ve gone through both lists.

4. **Result**
   - Merged is a list of up to 100 **unique** chunk IDs, with a bias toward BM25 results (they appear first) and no score fusion. This list is then passed to the MedCPT Cross-Encoder for reranking; the reranker produces the final ordering and we return the **top-N** (e.g. 8) by reranker score.

So: **merge = “BM25 list then dense list, drop duplicates, cap at K_MERGE.”** Final ranking is done by the reranker, not by the merge step.

---

## Summary

| Component              | When it runs     | What it does                                      |
|------------------------|------------------|---------------------------------------------------|
| BM25                   | Index + query    | Keyword-style candidate retrieval                 |
| MedCPT Article Encoder | Index only       | Encode chunks → vectors stored in ChromaDB        |
| MedCPT Query Encoder   | Query only       | Encode query → vector for similarity search        |
| MedCPT Cross-Encoder   | Query only       | Rerank (query, chunk) pairs for final top-N       |
