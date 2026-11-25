"use client";

import React from "react";

interface UserBubbleProps {
  content: string;
  timestamp: number;
}

export const UserBubble: React.FC<UserBubbleProps> = ({ content, timestamp }) => {
  const formattedTime = new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="flex justify-end w-full my-3">
      <div className="max-w-[85%] sm:max-w-[80%] rounded-2xl rounded-tr-sm bg-garage-900 dark:bg-garage-100 text-white dark:text-garage-900 px-4 py-3 border border-garage-800 dark:border-garage-200 shadow-sm">
        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words font-normal">
          {content}
        </p>
        <div className="text-[11px] text-garage-400 dark:text-garage-600 text-right mt-1.5">
          {formattedTime}
        </div>
      </div>
    </div>
  );
};
