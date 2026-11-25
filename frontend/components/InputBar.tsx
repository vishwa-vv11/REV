"use client";

import React, { useRef } from "react";
import { Paperclip, ArrowUp } from "lucide-react";

interface InputBarProps {
  input: string;
  setInput: (val: string) => void;
  onSend: () => void;
  disabled?: boolean;
  onPdfAttached?: (filename: string) => void;
}

export const InputBar: React.FC<InputBarProps> = ({
  input,
  setInput,
  onSend,
  disabled = false,
  onPdfAttached,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onPdfAttached) {
      onPdfAttached(file.name);
    }
    // reset input so the same file can be reselected if needed
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full bg-white dark:bg-garage-950 border-t border-garage-200 dark:border-garage-800 p-2 sm:p-3">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSend();
        }}
        className="flex items-center gap-2 rounded-2xl border border-garage-300 dark:border-garage-700 bg-garage-50 dark:bg-garage-900 px-3 py-1.5 focus-within:border-garage-500 focus-within:ring-1 focus-within:ring-garage-500 transition-all shadow-inner"
      >
        {/* Hidden PDF file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Upload PDF repair manual"
        />

        {/* Attach File Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="p-2 rounded-full text-garage-500 hover:text-garage-800 dark:text-garage-400 dark:hover:text-garage-100 hover:bg-garage-200/60 dark:hover:bg-garage-800 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-garage-400"
          aria-label="Attach OEM PDF service manual"
          title="Upload OEM service manual (PDF)"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Text Input */}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask diagnosis or code (e.g., P0301)..."
          className="flex-1 bg-transparent border-none outline-none text-xs sm:text-sm text-garage-900 dark:text-garage-100 placeholder-garage-400 dark:placeholder-garage-500 py-2.5 px-1 min-h-[40px]"
          aria-label="Diagnostic inquiry input"
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="p-2 rounded-full bg-garage-900 text-white dark:bg-garage-100 dark:text-garage-900 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-garage-800 dark:hover:bg-white transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-garage-400 shrink-0"
          aria-label="Send diagnostic question"
        >
          <ArrowUp className="w-4 h-4 stroke-[2.5]" />
        </button>
      </form>
    </div>
  );
};
