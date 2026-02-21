# Atheria — Biochem Paper Section Finder MVP

A retrieval-first system that finds relevant sections of biochemistry/biomedical papers for metric-baseline queries, using BM25 + MedCPT dense retriever + MedCPT reranker.

## Features

- **Section pointing**: Returns top sections/paragraphs where papers define, compute, or report evaluation metrics
- **Evidence-first**: Includes verbatim snippets, section path, and page numbers
- **Hybrid retrieval**: BM25 + MedCPT dense + MedCPT reranker for high recall and precision
- **Table-aware**: Treats tables and captions as first-class chunks

## Setup

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Build index from a paper (PMC XML/HTML or local file)

```bash
python -m atheria.index.build_index --input data/raw/paper.xml --output data/index
```

### Query via CLI

```bash
python -m atheria.api.app query "electrophysiology assessment metrics"
```

### Streamlit UI

```bash
streamlit run frontend/app.py
```

Run from the project root. Ensure the index is built first.

### Run evaluation

```bash
python eval/evaluate.py
```

## Seed Paper

"Induced pluripotent stem cell-derived cardiomyocyte in vitro models: benchmarking progress and ongoing challenges" (Nature Methods 2025, DOI: 10.1038/s41592-024-02480-7)
