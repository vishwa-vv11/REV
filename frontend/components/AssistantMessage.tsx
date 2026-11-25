"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, Cpu } from "lucide-react";
import { Message } from "../types";
import { Checklist } from "./Checklist";
import { SafetyCallout } from "./SafetyCallout";
import { AbstentionCard } from "./AbstentionCard";

interface AssistantMessageProps {
  message: Message;
  checkedSteps: Record<string, boolean>;
  onToggleStep: (key: string) => void;
  onSelectSource?: (sourceId: string) => void;
  onUploadManual?: () => void;
  onRecheckCode?: () => void;
  activeSourceId?: string | null;
}

export const AssistantMessage: React.FC<AssistantMessageProps> = ({
  message,
  checkedSteps,
  onToggleStep,
  onSelectSource,
  onUploadManual = () => {},
  onRecheckCode = () => {},
  activeSourceId,
}) => {
  const { diagnosis, visibleWords = 999, showChecklist = true, showMeta = true } = message;

  if (!diagnosis) {
    return (
      <div className="w-full my-3 text-left">
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-garage-900 border border-garage-200 dark:border-garage-800 p-4 text-xs text-garage-500">
          Loading diagnostic response...
        </div>
      </div>
    );
  }

  // 1. Blocked State
  if (diagnosis.status === "blocked") {
    return (
      <div className="w-full my-3 text-left" aria-live="polite">
        <div className="rounded-2xl rounded-tl-sm bg-garage-100 dark:bg-garage-900 border border-garage-200 dark:border-garage-800 p-4 text-xs text-garage-600 dark:text-garage-400 leading-relaxed shadow-sm">
          {diagnosis.summary}
        </div>
      </div>
    );
  }

  // 2. Abstained State
  if (diagnosis.status === "abstained") {
    return (
      <div className="w-full my-3" aria-live="polite">
        {showMeta && (
          <div className="flex items-center gap-1.5 text-[11px] text-garage-500 dark:text-garage-400 mb-1.5 px-1 font-mono">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
            <span>Checked {diagnosis.chunksSearched.toLocaleString()} chunks, 0 matched, {diagnosis.latencyMs} ms</span>
          </div>
        )}
        <AbstentionCard
          summary={diagnosis.summary}
          onUploadManual={onUploadManual}
          onRecheckCode={onRecheckCode}
        />
      </div>
    );
  }

  // 3. Answered State
  // Word-by-word streaming simulation
  const summaryWords = diagnosis.summary.split(" ");
  const displayedSummary = message.streaming
    ? summaryWords.slice(0, visibleWords).join(" ")
    : diagnosis.summary;

  return (
    <div className="w-full my-3 text-left space-y-3" aria-live="polite">
      {/* 1. Meta Line */}
      {showMeta && (
        <div className="flex items-center gap-1.5 text-[11px] text-garage-500 dark:text-garage-400 px-1 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>
            Checked {diagnosis.chunksSearched.toLocaleString()} chunks, {diagnosis.sources.length} sources, {diagnosis.latencyMs} ms
          </span>
        </div>
      )}

      {/* Main Answer Card */}
      <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-garage-900 border border-garage-200 dark:border-garage-800 p-4 sm:p-5 shadow-sm space-y-3">
        {/* 2. Short Summary Paragraph */}
        <p className="text-xs sm:text-sm text-garage-800 dark:text-garage-100 leading-relaxed font-normal">
          {displayedSummary}
          {message.streaming && visibleWords < summaryWords.length && (
            <span className="inline-block w-1.5 h-3.5 ml-1 bg-garage-400 dark:bg-garage-500 animate-pulse"></span>
          )}
        </p>

        {/* 3 & 4. Interactive Repair Checklist */}
        {showChecklist && diagnosis.steps.length > 0 && (
          <Checklist
            messageId={message.id}
            steps={diagnosis.steps}
            sources={diagnosis.sources}
            checkedSteps={checkedSteps}
            onToggleStep={onToggleStep}
            onSelectSource={onSelectSource}
            activeSourceId={activeSourceId}
          />
        )}

        {/* 5. Safety Callout (Amber) */}
        {showChecklist && diagnosis.safetyNotes.length > 0 && (
          <SafetyCallout notes={diagnosis.safetyNotes} />
        )}

        {/* 6. Status Chips */}
        {showChecklist && (
          <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-garage-100 dark:border-garage-800">
            {diagnosis.checks.groundingPassed && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-revGreen-light text-revGreen-text border border-revGreen-border dark:bg-revGreen-darkBg dark:text-revGreen-darkText dark:border-revGreen-darkBorder">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Grounding audit passed
              </span>
            )}
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-garage-100 text-garage-600 border border-garage-200 dark:bg-garage-800 dark:text-garage-400 dark:border-garage-700">
              Sample data
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono text-garage-500 dark:text-garage-400">
              <Cpu className="w-3 h-3" />
              Llama 3.2
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
