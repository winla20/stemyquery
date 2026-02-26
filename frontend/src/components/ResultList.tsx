import type { SectionPointer } from "../types";
import { ResultCard } from "./ResultCard";

interface Props {
  results: SectionPointer[];
  queryUsed: string;
  onOpenContext: (chunkId: string) => void;
}

export function ResultList({ results, queryUsed, onOpenContext }: Props) {
  if (results.length === 0) {
    return <p style={{ color: "#6b7280" }}>No results found.</p>;
  }
  return (
    <div>
      <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 12 }}>
        {results.length} result{results.length !== 1 ? "s" : ""} for:{" "}
        <em>{queryUsed}</em>
      </p>
      {results.map((r, i) => (
        <ResultCard
          key={r.chunk_id}
          result={r}
          rank={i + 1}
          onOpenContext={onOpenContext}
        />
      ))}
    </div>
  );
}
