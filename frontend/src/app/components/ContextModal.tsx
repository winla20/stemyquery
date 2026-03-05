import { X } from "lucide-react";
import { useChunkContext } from "../../hooks/useChunkContext";
import type { ChunkOut } from "../../types";

interface ContextModalProps {
  chunkId: string;
  onClose: () => void;
}

function ChunkBlock({ chunk, isCurrent }: { chunk: ChunkOut; isCurrent?: boolean }) {
  return (
    <div
      className={`p-4 rounded-lg border ${
        isCurrent
          ? "border-slate-400 bg-slate-50"
          : "border-gray-200 bg-white opacity-70"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-slate-500 uppercase tracking-wider">
          {chunk.section_path.join(" › ")}
        </span>
        {isCurrent && (
          <span className="text-xs bg-slate-800 text-white px-2 py-0.5 rounded">
            Selected
          </span>
        )}
      </div>
      <p
        className="text-sm leading-relaxed text-gray-800"
        style={{ fontFamily: "Georgia, serif" }}
      >
        {chunk.text}
      </p>
      <p className="text-xs text-gray-400 mt-2">
        Pages {chunk.page_start}–{chunk.page_end} • {chunk.chunk_type}
      </p>
    </div>
  );
}

export function ContextModal({ chunkId, onClose }: ContextModalProps) {
  const { context, isLoading, error } = useChunkContext(chunkId);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-gray-200">
          <h2 className="text-base font-semibold text-slate-800">Full Context</h2>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {isLoading && (
            <div className="flex items-center justify-center py-12 text-sm text-gray-500">
              Loading context...
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {context && (
            <>
              {context.prev && (
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Previous</p>
                  <ChunkBlock chunk={context.prev} />
                </div>
              )}
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Current</p>
                <ChunkBlock chunk={context.current} isCurrent />
              </div>
              {context.next && (
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Next</p>
                  <ChunkBlock chunk={context.next} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
