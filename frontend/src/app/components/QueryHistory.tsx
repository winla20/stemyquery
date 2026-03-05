import { useState } from "react";
import { Search, Clock, ChevronRight } from "lucide-react";
import type { HistoryItem } from "../pages/ResearchMode";

interface QueryHistoryProps {
  history: HistoryItem[];
  onSelect: (item: HistoryItem) => void;
}

export function QueryHistory({ history, onSelect }: QueryHistoryProps) {
  const [filter, setFilter] = useState("");

  const filtered = history.filter((item) =>
    item.query.toLowerCase().includes(filter.toLowerCase())
  );

  function formatTime(date: Date): string {
    const diff = Date.now() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="text-sm uppercase tracking-wider text-gray-600 mb-3">
          Query History
        </h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search queries..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="p-6 text-center text-sm text-gray-500">
            {history.length === 0
              ? "No queries yet. Search above to get started."
              : "No matching queries."}
          </div>
        )}
        {filtered.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            className="w-full p-4 border-b border-gray-200 hover:bg-white transition-colors text-left group"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <p className="text-sm text-gray-900 line-clamp-2 flex-1">{item.query}</p>
              <ChevronRight className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              {formatTime(item.timestamp)}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
