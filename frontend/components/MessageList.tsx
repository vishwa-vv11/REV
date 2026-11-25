"use client";

import React, { useEffect, useRef } from "react";
import { Message } from "../types";
import { UserBubble } from "./UserBubble";
import { AssistantMessage } from "./AssistantMessage";

interface MessageListProps {
  messages: Message[];
  checkedSteps: Record<string, boolean>;
  onToggleStep: (key: string) => void;
  onSelectSource?: (sourceId: string) => void;
  onUploadManual?: () => void;
  onRecheckCode?: () => void;
  activeSourceId?: string | null;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  checkedSteps,
  onToggleStep,
  onSelectSource,
  onUploadManual,
  onRecheckCode,
  activeSourceId,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 space-y-4">
      {messages.map((msg) => (
        <React.Fragment key={msg.id}>
          {msg.role === "user" ? (
            <UserBubble content={msg.content} timestamp={msg.timestamp} />
          ) : (
            <AssistantMessage
              message={msg}
              checkedSteps={checkedSteps}
              onToggleStep={onToggleStep}
              onSelectSource={onSelectSource}
              onUploadManual={onUploadManual}
              onRecheckCode={onRecheckCode}
              activeSourceId={activeSourceId}
            />
          )}
        </React.Fragment>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
