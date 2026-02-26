import { useState } from "react";
import { postQuery } from "../api/client";
import type { QueryResponse } from "../types";

interface SearchParams {
  query: string;
  paperId?: string;
  topN?: number;
}

export function useQuery() {
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search({ query, paperId, topN }: SearchParams) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await postQuery({
        query,
        paper_id: paperId || undefined,
        top_n: topN,
      });
      setResults(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setIsLoading(false);
    }
  }

  return { results, isLoading, error, search };
}
