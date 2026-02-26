export interface SectionPointer {
  paper_title: string;
  paper_id: string;
  pmid: string | null;
  doi: string | null;
  section_path: string;
  page_start: number;
  page_end: number;
  snippets: string[];
  confidence: "high" | "med" | "low";
  chunk_id: string;
  reranker_score: number;
}

export interface QueryResponse {
  results: SectionPointer[];
  query_used: string;
  total: number;
}

export interface Paper {
  paper_id: string;
  title: string;
  pmid: string | null;
  doi: string | null;
  source_url: string | null;
  chunk_count: number;
}

export interface ChunkOut {
  chunk_id: string;
  paper_id: string;
  chunk_type: string;
  section_path: string[];
  page_start: number;
  page_end: number;
  text: string;
}

export interface ChunkContextOut {
  prev: ChunkOut | null;
  current: ChunkOut;
  next: ChunkOut | null;
}
