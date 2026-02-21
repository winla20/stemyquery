"""Configuration for retrieval and indexing."""

from pathlib import Path

# Retrieval parameters
K_SPARSE = 50
K_DENSE = 50
K_MERGE = 100
TOP_N = 8

# MedCPT models
MEDCPT_ARTICLE_ENCODER = "ncbi/MedCPT-Article-Encoder"
MEDCPT_QUERY_ENCODER = "ncbi/MedCPT-Query-Encoder"
MEDCPT_CROSS_ENCODER = "ncbi/MedCPT-Cross-Encoder"

# Paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INDEX_DIR = DATA_DIR / "index"
CHROMA_PATH = str(INDEX_DIR / "chroma")
BM25_PATH = str(INDEX_DIR / "bm25")
CHUNKS_PATH = str(INDEX_DIR / "chunks.json")
PAPERS_PATH = str(INDEX_DIR / "papers.json")
