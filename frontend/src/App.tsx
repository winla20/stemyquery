import { useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { ResultList } from "./components/ResultList";
import { ContextViewer } from "./components/ContextViewer";
import { usePapers } from "./hooks/usePapers";
import { useQuery } from "./hooks/useQuery";
import "./styles/index.css";

export default function App() {
  const { papers } = usePapers();
  const { results, isLoading, error, search } = useQuery();
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);

  function handleSearch(query: string, paperId: string, topN: number) {
    search({ query, paperId: paperId || undefined, topN });
  }

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4, color: "#111827" }}>
        Atheria Section Finder
      </h1>
      <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 24 }}>
        Find relevant sections of biomedical papers for metric baseline queries.
      </p>

      <SearchBar papers={papers} isLoading={isLoading} onSearch={handleSearch} />

      {error && (
        <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: 6, padding: "10px 14px", marginBottom: 16, color: "#991b1b", fontSize: 13 }}>
          {error}
        </div>
      )}

      {results && (
        <ResultList
          results={results.results}
          queryUsed={results.query_used}
          onOpenContext={setSelectedChunkId}
        />
      )}

      {selectedChunkId && (
        <ContextViewer
          chunkId={selectedChunkId}
          onClose={() => setSelectedChunkId(null)}
        />
      )}
    </div>
  );
}
