import { useEffect, useState } from "react";
import { getChunkContext } from "../api/client";
import type { ChunkContextOut } from "../types";

export function useChunkContext(chunkId: string | null) {
  const [context, setContext] = useState<ChunkContextOut | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chunkId) {
      setContext(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    getChunkContext(chunkId)
      .then(setContext)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setIsLoading(false));
  }, [chunkId]);

  return { context, isLoading, error };
}
