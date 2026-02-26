import type { ChunkContextOut, Paper, QueryResponse } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function postQuery(params: {
  query: string;
  paper_id?: string;
  top_n?: number;
  use_query_expansion?: boolean;
}): Promise<QueryResponse> {
  return request<QueryResponse>("/api/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export async function getPapers(): Promise<Paper[]> {
  return request<Paper[]>("/api/papers");
}

export async function getChunkContext(chunkId: string): Promise<ChunkContextOut> {
  return request<ChunkContextOut>(`/api/chunks/${encodeURIComponent(chunkId)}/context`);
}
