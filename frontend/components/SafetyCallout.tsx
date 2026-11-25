"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";

interface SafetyCalloutProps {
  notes: string[];
}

export const SafetyCallout: React.FC<SafetyCalloutProps> = ({ notes }) => {
  if (!notes || notes.length === 0) return null;

  return (
    <div
      role="alert"
      className="rounded-xl border border-revAmber-border dark:border-revAmber-darkBorder bg-revAmber-light dark:bg-revAmber-darkBg p-3.5 my-3 text-xs leading-relaxed"
    >
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
        <div className="space-y-1 text-revAmber-text dark:text-revAmber-darkText">
          <div className="font-semibold text-xs tracking-wide uppercase">
            Safety Precaution
          </div>
          {notes.map((note, idx) => (
            <p key={idx} className="text-xs">
              {note}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
};
