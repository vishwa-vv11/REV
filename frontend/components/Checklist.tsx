"use client";

import React, { useState } from "react";
import { CitationChip } from "./CitationChip";
import { ChevronDown, ChevronUp, BookOpen, Clock } from "lucide-react";
import { Diagnosis } from "../types";

interface ChecklistProps {
  messageId: string;
  steps: Diagnosis["steps"];
  sources: Diagnosis["sources"];
  checkedSteps: Record<string, boolean>;
  onToggleStep: (key: string) => void;
  onSelectSource?: (sourceId: string) => void;
  activeSourceId?: string | null;
}

export const Checklist: React.FC<ChecklistProps> = ({
  messageId,
  steps,
  sources,
  checkedSteps,
  onToggleStep,
  onSelectSource,
  activeSourceId,
}) => {
  const [expandedSourceId, setExpandedSourceId] = useState<string | null>(null);
  const [showParentFor, setShowParentFor] = useState<Record<string, boolean>>({});

  const handleCitationClick = (sourceId: string) => {
    setExpandedSourceId((prev) => (prev === sourceId ? null : sourceId));
    if (onSelectSource) {
      onSelectSource(sourceId);
    }
  };

  const toggleParentText = (sourceId: string) => {
    setShowParentFor((prev) => ({
      ...prev,
      [sourceId]: !prev[sourceId],
    }));
  };

  const totalSteps = steps.length;
  const completedCount = steps.filter(
    (step) => checkedSteps[`${messageId}_step_${step.order}`]
  ).length;

  return (
    <div className="space-y-3 my-3">
      {/* Progress Counter */}
      {totalSteps > 0 && (
        <div className="flex items-center justify-between text-xs font-medium text-garage-500 dark:text-garage-400 px-0.5">
          <span>Repair checklist</span>
          <span className="font-mono">
            {completedCount} of {totalSteps} done
          </span>
        </div>
      )}

      {/* Steps List */}
      <div className="space-y-2.5">
        {steps.map((step) => {
          const stepKey = `${messageId}_step_${step.order}`;
          const isChecked = !!checkedSteps[stepKey];

          return (
            <div
              key={step.order}
              className={`rounded-xl border p-3 transition-colors ${
                isChecked
                  ? "bg-garage-50 dark:bg-garage-900/40 border-garage-200 dark:border-garage-800"
                  : "bg-white dark:bg-garage-900 border-garage-200 dark:border-garage-700 shadow-sm"
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Real checkbox with accessible tap target */}
                <div className="pt-0.5 min-w-[28px] min-h-[28px] flex items-center justify-center">
                  <input
                    type="checkbox"
                    id={stepKey}
                    checked={isChecked}
                    onChange={() => onToggleStep(stepKey)}
                    className="w-4 h-4 rounded text-garage-900 dark:text-garage-100 bg-white dark:bg-garage-800 border-garage-300 dark:border-garage-600 focus:ring-2 focus:ring-garage-500 cursor-pointer"
                    aria-label={`Mark step ${step.order} as completed`}
                  />
                </div>

                <div className="flex-1 space-y-2">
                  <label
                    htmlFor={stepKey}
                    className={`block text-xs sm:text-sm leading-relaxed cursor-pointer transition-colors ${
                      isChecked
                        ? "line-through text-garage-400 dark:text-garage-500"
                        : "text-garage-800 dark:text-garage-100 font-normal"
                    }`}
                  >
                    <span className="font-semibold text-garage-900 dark:text-garage-100 mr-1.5">
                      Step {step.order}.
                    </span>
                    {step.text}
                  </label>

                  {/* Metadata & Citations Row */}
                  <div className="flex flex-wrap items-center gap-2 pt-0.5">
                    {step.laborHours && (
                      <span className="inline-flex items-center gap-1 text-[11px] text-garage-500 dark:text-garage-400">
                        <Clock className="w-3 h-3" />
                        {step.laborHours} hr
                      </span>
                    )}

                    {step.sourceIds?.map((srcId) => (
                      <CitationChip
                        key={srcId}
                        sourceId={srcId}
                        onClick={handleCitationClick}
                        isActive={
                          expandedSourceId === srcId || activeSourceId === srcId
                        }
                      />
                    ))}
                  </div>

                  {/* Inline Expanded Source Chunk View */}
                  {expandedSourceId &&
                    step.sourceIds?.includes(expandedSourceId) && (
                      <div className="mt-2.5 p-3 rounded-lg bg-garage-100/90 dark:bg-garage-950/80 border border-garage-200 dark:border-garage-800 text-xs space-y-2">
                        {(() => {
                          const src = sources.find(
                            (s) => s.id === expandedSourceId
                          );
                          if (!src) return null;
                          const showParent = showParentFor[src.id];

                          return (
                            <>
                              <div className="flex items-center justify-between text-[11px] font-mono text-garage-500 dark:text-garage-400 border-b border-garage-200 dark:border-garage-800 pb-1.5">
                                <span>Source: {src.id}</span>
                                <span>Rank #{src.rank} (Score: {src.score})</span>
                              </div>

                              <div className="text-garage-700 dark:text-garage-300 font-mono text-[11px] leading-relaxed">
                                {showParent ? src.parentText : src.chunkText}
                              </div>

                              <button
                                type="button"
                                onClick={() => toggleParentText(src.id)}
                                className="inline-flex items-center gap-1 text-[11px] font-medium text-revBlue-text dark:text-revBlue-darkText hover:underline pt-1 focus:outline-none focus:ring-2 focus:ring-revBlue-border rounded"
                              >
                                <BookOpen className="w-3 h-3" />
                                <span>
                                  {showParent
                                    ? "Hide parent guide"
                                    : "Show parent guide"}
                                </span>
                                {showParent ? (
                                  <ChevronUp className="w-3 h-3" />
                                ) : (
                                  <ChevronDown className="w-3 h-3" />
                                )}
                              </button>
                            </>
                          );
                        })()}
                      </div>
                    )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
