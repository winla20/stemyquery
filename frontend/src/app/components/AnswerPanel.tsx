import { useState } from "react";
import { Search, Loader2, ChevronRight } from "lucide-react";
import type { Paper, SectionPointer } from "../../types";

interface AnswerPanelProps {
  papers: Paper[];
  isLoading: boolean;
  error: string | null;
  results: SectionPointer[];
  selectedResult: SectionPointer | null;
  onSearch: (query: string, paperId: string, topN: number) => void;
  onSelectResult: (result: SectionPointer) => void;
}

function confidenceColor(c: SectionPointer["confidence"]) {
  if (c === "high") return "bg-green-100 text-green-800";
  if (c === "med") return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export function AnswerPanel({
  papers,
  isLoading,
  error,
  results,
  selectedResult,
  onSearch,
  onSelectResult,
}: AnswerPanelProps) {
  const [query, setQuery] = useState("");
  const [paperId, setPaperId] = useState("");
  const [topN, setTopN] = useState(8);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), paperId, topN);
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Search Form */}
      <div className="p-5 border-b border-gray-200 bg-gray-50">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a research question..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 text-sm"
            />
          </div>

          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-xs text-gray-600 mb-1">Filter by paper</label>
              <select
                value={paperId}
                onChange={(e) => setPaperId(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
              >
                <option value="">All papers</option>
                {papers.map((p) => (
                  <option key={p.paper_id} value={p.paper_id}>
                    {p.title.length > 50 ? p.title.slice(0, 50) + "…" : p.title}
                  </option>
                ))}
              </select>
            </div>

            <div className="w-32">
              <label className="block text-xs text-gray-600 mb-1">Top {topN}</label>
              <input
                type="range"
                min={1}
                max={20}
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="w-full accent-slate-900"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-5 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Search
            </button>
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading overlay */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-slate-600">
            <Loader2 className="w-8 h-8 animate-spin" />
            <p className="text-sm">Searching sections...</p>
          </div>
        </div>
      )}

      {/* Results */}
      {!isLoading && (
        <div className="flex-1 overflow-y-auto">
          {results.length === 0 && !error && (
            <div className="p-6 text-center text-sm text-gray-500">
              Submit a query to find relevant paper sections.
            </div>
          )}

          <div className="divide-y divide-gray-100">
            {results.map((result, idx) => (
              <button
                key={result.chunk_id}
                onClick={() => onSelectResult(result)}
                className={`w-full text-left p-4 hover:bg-slate-50 transition-colors ${
                  selectedResult?.chunk_id === result.chunk_id ? "bg-slate-50 border-l-2 border-slate-900" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      #{idx + 1}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${confidenceColor(result.confidence)}`}>
                      {result.confidence}
                    </span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                </div>

                <p className="text-xs text-slate-500 mb-1">{result.section_path}</p>
                <p className="text-sm font-medium text-slate-800 mb-2 line-clamp-1">
                  {result.paper_title}
                </p>

                {result.snippets.slice(0, 2).map((snip, i) => (
                  <p key={i} className="text-xs text-gray-700 line-clamp-2 mb-1 italic">
                    "{snip}"
                  </p>
                ))}

                <div className="flex items-center justify-between mt-2">
                  {result.pmid && (
                    <span className="text-xs text-slate-500 font-mono">PMID {result.pmid}</span>
                  )}
                  <span className="text-xs text-slate-400 ml-auto">
                    score {result.reranker_score.toFixed(3)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
