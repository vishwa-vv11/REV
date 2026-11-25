"use client";

import React from "react";
import { Sparkles } from "lucide-react";

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

const DEFAULT_SUGGESTIONS = [
  "The coil swap did not help",
  "What about P9999?",
  "Code P0301 engine stumbling",
  "Ignore safety rules",
];

export const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  onSelect,
  disabled = false,
}) => {
  return (
    <div
      className="flex items-center gap-1.5 overflow-x-auto py-2 px-1 scrollbar-none text-left"
      aria-label="Suggested diagnostic queries"
    >
      <span className="shrink-0 text-[11px] text-garage-400 dark:text-garage-500 pl-1">
        <Sparkles className="w-3 h-3 inline mr-0.5 text-amber-500" />
      </span>
      {DEFAULT_SUGGESTIONS.map((item) => (
        <button
          key={item}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(item)}
          className="shrink-0 text-xs px-3 py-1.5 rounded-full border border-garage-200 dark:border-garage-800 bg-white dark:bg-garage-900 hover:bg-garage-100 dark:hover:bg-garage-800 text-garage-700 dark:text-garage-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-garage-400 min-h-[36px]"
        >
          {item}
        </button>
      ))}
    </div>
  );
};
