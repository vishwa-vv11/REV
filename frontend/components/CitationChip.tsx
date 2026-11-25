"use client";

import React from "react";
import { FileText } from "lucide-react";

interface CitationChipProps {
  sourceId: string;
  onClick: (sourceId: string) => void;
  isActive?: boolean;
}

export const CitationChip: React.FC<CitationChipProps> = ({
  sourceId,
  onClick,
  isActive = false,
}) => {
  return (
    <button
      type="button"
      onClick={() => onClick(sourceId)}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-medium border transition-colors min-h-[28px] focus:outline-none focus:ring-2 focus:ring-revBlue-border ${
        isActive
          ? "bg-revBlue-text text-white border-revBlue-text dark:bg-revBlue-darkText dark:text-garage-950"
          : "bg-revBlue-light text-revBlue-text border-revBlue-border hover:bg-blue-100 dark:bg-revBlue-darkBg dark:text-revBlue-darkText dark:border-revBlue-darkBorder dark:hover:bg-sky-950/80"
      }`}
      aria-label={`Citation reference ${sourceId}. Click to inspect source chunk`}
    >
      <FileText className="w-3 h-3" />
      <span>{sourceId}</span>
    </button>
  );
};
