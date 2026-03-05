import { useState } from "react";
import { Search, Tag, FileText, ArrowLeft, BookOpen } from "lucide-react";
import { useNavigate } from "react-router";
import { usePapers } from "../../hooks/usePapers";
import { useTopics } from "../../hooks/useTopics";
import type { Topic, PaperGroup, TopicChunk } from "../../types";

function getSizeTier(count: number, topics: Topic[]): string {
  const counts = topics.map((t) => t.chunk_count).sort((a, b) => a - b);
  const p66 = counts[Math.floor(counts.length * 0.66)] ?? 0;
  const p33 = counts[Math.floor(counts.length * 0.33)] ?? 0;
  if (count >= p66) return "text-lg font-semibold";
  if (count >= p33) return "text-base font-medium";
  return "text-sm";
}

function TopicChip({
  topic,
  allTopics,
  onClick,
}: {
  topic: Topic;
  allTopics: Topic[];
  onClick: () => void;
}) {
  const size = getSizeTier(topic.chunk_count, allTopics);
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-full hover:border-slate-400 hover:shadow-sm transition-all cursor-pointer ${size}`}
    >
      <span className="text-slate-700">{topic.topic}</span>
      <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full">
        {topic.chunk_count}
      </span>
    </button>
  );
}

function ChunkSnippet({
  chunk,
  onClick,
}: {
  chunk: TopicChunk;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="text-left w-full p-3 bg-slate-50 border border-slate-100 rounded-md hover:border-slate-300 hover:bg-white transition-all cursor-pointer"
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-xs text-slate-400 font-mono">
          {chunk.section_path.join(" > ")}
        </span>
        <span className="text-xs text-slate-400">
          pp. {chunk.page_start}–{chunk.page_end}
        </span>
      </div>
      <p className="text-sm text-slate-600 line-clamp-3">{chunk.snippet}</p>
    </button>
  );
}

function PaperGroupCard({
  group,
  onChunkClick,
}: {
  group: PaperGroup;
  onChunkClick: (paperId: string) => void;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5">
      <div className="mb-3">
        <h3 className="font-serif text-slate-800 text-base leading-snug mb-1">
          {group.paper_title}
        </h3>
        <div className="flex items-center gap-2">
          {group.pmid && (
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
              PMID {group.pmid}
            </span>
          )}
          {group.doi && (
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
              DOI {group.doi}
            </span>
          )}
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {group.chunks.map((chunk) => (
          <ChunkSnippet
            key={chunk.chunk_id}
            chunk={chunk}
            onClick={() => onChunkClick(group.paper_id)}
          />
        ))}
      </div>
    </div>
  );
}

export default function DiscoveryMode() {
  const { papers } = usePapers();
  const { topics, selectedDrillDown, loading, error, selectTopic, clearSelection } = useTopics();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTopics = topics.filter((t) =>
    t.topic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (selectedDrillDown) {
    return (
      <div className="size-full bg-slate-50 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-8 py-8">
          <button
            onClick={clearSelection}
            className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-800 mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to topics
          </button>

          <div className="mb-8">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-serif text-slate-800">
                {selectedDrillDown.topic}
              </h1>
              <span className="text-sm bg-slate-200 text-slate-600 px-2.5 py-1 rounded-full">
                {selectedDrillDown.total_chunks} chunks
              </span>
            </div>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="w-6 h-6 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-6">
            {selectedDrillDown.papers.map((group) => (
              <PaperGroupCard
                key={group.paper_id}
                group={group}
                onChunkClick={(paperId) => navigate(`/?paper=${paperId}`)}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="size-full bg-slate-50 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-slate-800 mb-2">Explore Topics</h1>
          <p className="text-slate-600">
            Browse section headings extracted from indexed papers. Click a topic to see matching chunks.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag className="w-5 h-5 text-slate-600" />
              <span className="text-sm text-slate-600">Topics</span>
            </div>
            <p className="text-2xl font-semibold text-slate-800">{topics.length}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-5 h-5 text-slate-600" />
              <span className="text-sm text-slate-600">Papers</span>
            </div>
            <p className="text-2xl font-semibold text-slate-800">{papers.length}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-5 h-5 text-slate-600" />
              <span className="text-sm text-slate-600">Avg Topics/Paper</span>
            </div>
            <p className="text-2xl font-semibold text-slate-800">
              {papers.length > 0 ? Math.round(topics.length / papers.length) : 0}
            </p>
          </div>
        </div>

        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Filter topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 text-slate-800 bg-white"
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 text-sm">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
          </div>
        )}

        {!loading && topics.length === 0 && !error && (
          <div className="text-center py-16">
            <p className="text-slate-500">No topics found. Index some papers first.</p>
          </div>
        )}

        {!loading && (
          <div className="flex flex-wrap gap-2">
            {filteredTopics.map((topic) => (
              <TopicChip
                key={topic.topic}
                topic={topic}
                allTopics={topics}
                onClick={() => selectTopic(topic.topic)}
              />
            ))}
          </div>
        )}

        {!loading && filteredTopics.length === 0 && topics.length > 0 && (
          <div className="text-center py-12">
            <p className="text-slate-500">No topics match your search.</p>
          </div>
        )}
      </div>
    </div>
  );
}
