import { useEffect, useState } from "react";
import { getPapers } from "../api/client";
import type { Paper } from "../types";

export function usePapers() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPapers()
      .then(setPapers)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return { papers, error };
}
