import { useState } from "react";
import { QueryHistory } from "../components/QueryHistory";
import { AnswerPanel } from "../components/AnswerPanel";
import { EvidencePanel } from "../components/EvidencePanel";
import { ContextModal } from "../components/ContextModal";
import { usePapers } from "../../hooks/usePapers";
import { useQuery } from "../../hooks/useQuery";
import type { SectionPointer } from "../../types";

export interface HistoryItem {
  id: string;
  query: string;
  timestamp: Date;
  paperId: string;
  topN: number;
}

export default function ResearchMode() {
  const { papers } = usePapers();
  const { results, isLoading, error, search } = useQuery();
  const [queryHistory, setQueryHistory] = useState<HistoryItem[]>([]);
  const [selectedResult, setSelectedResult] = useState<SectionPointer | null>(null);
  const [contextChunkId, setContextChunkId] = useState<string | null>(null);

  function handleSearch(query: string, paperId: string, topN: number) {
    setQueryHistory((prev) => [
      { id: crypto.randomUUID(), query, timestamp: new Date(), paperId, topN },
      ...prev,
    ]);
    setSelectedResult(null);
    search({ query, paperId: paperId || undefined, topN });
  }

  function handleSelectHistory(item: HistoryItem) {
    setSelectedResult(null);
    search({ query: item.query, paperId: item.paperId || undefined, topN: item.topN });
  }

  return (
    <div className="size-full flex bg-white">
      <div className="w-80 h-full flex-shrink-0">
        <QueryHistory history={queryHistory} onSelect={handleSelectHistory} />
      </div>

      <div className="flex-1 h-full min-w-0">
        <AnswerPanel
          papers={papers}
          isLoading={isLoading}
          error={error}
          results={results?.results ?? []}
          onSearch={handleSearch}
          onSelectResult={setSelectedResult}
          selectedResult={selectedResult}
        />
      </div>

      <div className="w-[500px] h-full flex-shrink-0">
        <EvidencePanel
          results={results?.results ?? []}
          selectedResult={selectedResult}
          onOpenContext={setContextChunkId}
        />
      </div>

      {contextChunkId && (
        <ContextModal chunkId={contextChunkId} onClose={() => setContextChunkId(null)} />
      )}
    </div>
  );
}
