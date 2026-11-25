"use client";

import React, { useState } from "react";
import { Diagnosis } from "../types";
import { BookOpen, ChevronUp, ChevronDown, Layers, X } from "lucide-react";

interface SourcePanelProps {
  sources: Diagnosis["sources"];
  activeSourceId: string | null;
  onClose?: () => void;
}

export const SourcePanel: React.FC<SourcePanelProps> = ({
  sources,
  activeSourceId,
  onClose,
}) => {
  const [showParentFor, setShowParentFor] = useState<Record<string, boolean>>({});

  const toggleParentText = (id: string) => {
    setShowParentFor((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (!sources || sources.length === 0) {
    return (
      <aside
        className="h-full flex flex-col items-center justify-center p-6 text-center text-garage-400 dark:text-garage-500 border-l border-garage-200 dark:border-garage-800 bg-garage-50/50 dark:bg-garage-950/50"
        aria-label="Evidence side panel"
      >
        <Layers className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-xs">No technical records selected.</p>
        <p className="text-[11px] mt-1 text-garage-400">
          Click citation chips in the diagnostic checklist to inspect source text.
        </p>
      </aside>
    );
  }

  // Filter or prioritize active source
  const sortedSources = [...sources].sort((a, b) => {
    if (a.id === activeSourceId) return -1;
    if (b.id === activeSourceId) return 1;
    return a.rank - b.rank;
  });

  return (
    <aside
      className="h-full flex flex-col border-l border-garage-200 dark:border-garage-800 bg-white dark:bg-garage-950 overflow-hidden"
      aria-label="Evidence inspection panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-garage-200 dark:border-garage-800 bg-garage-50 dark:bg-garage-900/60">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-revBlue-text dark:text-revBlue-darkText" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-garage-800 dark:text-garage-200">
            Retrieved Evidence ({sources.length})
          </h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-garage-200 dark:hover:bg-garage-800 text-garage-500"
            aria-label="Close evidence panel"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Sources list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {sortedSources.map((source) => {
          const isSelected = source.id === activeSourceId;
          const showParent = showParentFor[source.id];

          return (
            <div
              key={source.id}
              className={`rounded-xl border p-3.5 transition-all text-left ${
                isSelected
                  ? "border-revBlue-border dark:border-revBlue-darkBorder bg-revBlue-light/40 dark:bg-revBlue-darkBg/30 ring-1 ring-revBlue-border"
                  : "border-garage-200 dark:border-garage-800 bg-garage-50 dark:bg-garage-900/40"
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-mono text-garage-500 dark:text-garage-400 border-b border-garage-200 dark:border-garage-800 pb-1.5 mb-2">
                <span className="font-semibold text-garage-900 dark:text-garage-100">
                  {source.id}
                </span>
                <span className="text-[10px]">
                  Rank #{source.rank} • Score: {source.score}
                </span>
              </div>

              <div className="text-xs text-garage-700 dark:text-garage-300 font-mono leading-relaxed whitespace-pre-wrap">
                {showParent ? source.parentText : source.chunkText}
              </div>

              <button
                type="button"
                onClick={() => toggleParentText(source.id)}
                className="mt-2.5 inline-flex items-center gap-1 text-[11px] font-medium text-revBlue-text dark:text-revBlue-darkText hover:underline focus:outline-none focus:ring-2 focus:ring-revBlue-border rounded"
              >
                <BookOpen className="w-3 h-3" />
                <span>
                  {showParent ? "View concise chunk" : "View full parent document"}
                </span>
                {showParent ? (
                  <ChevronUp className="w-3 h-3" />
                ) : (
                  <ChevronDown className="w-3 h-3" />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
};
