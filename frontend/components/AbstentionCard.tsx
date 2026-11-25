"use client";

import React from "react";
import { HelpCircle, Upload, Search } from "lucide-react";

interface AbstentionCardProps {
  summary: string;
  onUploadManual: () => void;
  onRecheckCode: () => void;
}

export const AbstentionCard: React.FC<AbstentionCardProps> = ({
  summary,
  onUploadManual,
  onRecheckCode,
}) => {
  return (
    <div
      role="region"
      aria-label="No valid data found notification"
      className="rounded-2xl border border-revAmber-border dark:border-revAmber-darkBorder bg-revAmber-light dark:bg-revAmber-darkBg p-4 sm:p-5 my-2 shadow-sm text-left"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-xl bg-amber-500/10 text-amber-700 dark:text-amber-400 shrink-0">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="space-y-2 flex-1">
          <h3 className="text-sm font-semibold text-revAmber-text dark:text-revAmber-darkText tracking-tight">
            No valid data found
          </h3>
          <p className="text-xs leading-relaxed text-amber-800/90 dark:text-amber-200/90">
            {summary ||
              "The technical knowledge base lacks verified service procedures for this specific diagnostic inquiry. The system abstained to prevent ungrounded repair advice."}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <button
              type="button"
              onClick={onUploadManual}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-600 hover:bg-amber-700 text-white shadow-sm transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload OEM manual</span>
            </button>
            <button
              type="button"
              onClick={onRecheckCode}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-400/80 dark:border-amber-700 bg-white/70 dark:bg-garage-900/60 text-amber-800 dark:text-amber-300 hover:bg-white dark:hover:bg-garage-900 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Recheck code</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
