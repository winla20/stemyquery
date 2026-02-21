# Verifying That Your Paper Was Indexed Correctly

Ways to check that a paper (e.g. `data/raw/ewoldt.htm`) was parsed, chunked, and indexed as expected.

---

## 1. Check the build output

When you run:

```bash
python -m atheria.api.app build --input data/raw/ewoldt.htm --output data/index
```

you should see something like:

```text
Indexed 1 paper(s), N chunk(s)
```

- **0 papers / 0 chunks** → The file wasn’t parsed (wrong format or parser couldn’t read it). Try opening the file and checking it’s valid HTML/XML; if you’re indexing a **directory**, ensure the file extension is picked up (e.g. use `*.htm` or `*.html`).
- **1 paper, N chunks** → At least one paper was parsed and split into N chunks. N in the dozens to hundreds is typical for a full article.

---

## 2. Check that index files exist

After a successful build, the output directory (default `data/index`) should contain:

| Path | Purpose |
|------|--------|
| `papers.json` | One entry per paper (title, paper_id, pmid, etc.). |
| `chunks.json` | All chunks with chunk_id, paper_id, section_path, text, etc. |
| `bm25/` | BM25 index (e.g. `corpus.pkl`, `chunk_ids.json`). |
| `chroma/` | Dense index (ChromaDB files). |

If any of these are missing or empty, indexing didn’t finish correctly.

---

## 3. Confirm your paper is in `papers.json`

Open `data/index/papers.json` and check that your article appears:

- **Title** matches the paper (or a sensible shortened version).
- **paper_id** is a UUID; you’ll use it to filter by paper when querying.

If you indexed a single file and don’t see your title, the parser likely failed on that file (see step 1).

---

## 4. Confirm chunks in `chunks.json`

Open `data/index/chunks.json`:

- **Count** how many chunks have the same `paper_id` as your paper. That’s how many sections/paragraphs/tables were indexed for that paper.
- **Spot-check** a few chunks:
  - `section_path`: e.g. `["Methods", "Electrophysiology"]` — does it match the document structure?
  - `text`: a short snippet of the paragraph or table — does it look correct and complete?
  - `chunk_type`: `"paragraph"`, `"table"`, `"caption"`, etc.

If section paths or text look wrong or empty, the parser may be misreading the HTML/XML structure.

---

## 5. Run a query that should hit your paper

Use a phrase or term you know appears in the paper, e.g. from the title or a key method:

```bash
python -m atheria.api.app query "electrophysiology assessment" --top 5
```

Or use the Streamlit UI and search for the same.

- **Your paper appears in the results** with the right section and snippets → indexing and retrieval are working for that paper.
- **Your paper never appears** → Try a more distinctive phrase, or filter by paper (in the UI or `--paper <paper_id>` in CLI). If it still doesn’t show, the chunk text or section paths may not match what you expect; re-check `chunks.json` for that paper_id.

---

## 6. Optional: quick script to summarize the index

From the project root you can run:

```bash
python -c "
import json
from pathlib import Path
idx = Path('data/index')
papers = json.loads((idx / 'papers.json').read_text())
chunks = json.loads((idx / 'chunks.json').read_text())
print('Papers:', len(papers))
for p in papers:
    pid = p['paper_id']
    n = sum(1 for c in chunks if c.get('paper_id') == pid)
    print(f\"  - {p['title'][:60]}... -> {n} chunks\")
print('Total chunks:', len(chunks))
"
```

This prints each indexed paper and how many chunks it has, so you can confirm your paper and chunk count at a glance.

---

## Summary

| What you want to verify | What to do |
|-------------------------|------------|
| File was accepted | Build prints “Indexed 1 paper(s), N chunk(s)” with N > 0. |
| Paper is in the index | Your title appears in `data/index/papers.json`. |
| Chunks look correct | Inspect `data/index/chunks.json` for your paper_id; check `section_path` and `text`. |
| Search finds the paper | Run a query with a distinctive phrase from the paper; it appears in results (or under that paper_id). |

If you index a **directory** (e.g. `--input data/raw`), the build step only picks up `*.xml`, `*.nxml`, `*.html`, and `*.htm` files. Your `ewoldt.htm` will be included when using that directory as input.
