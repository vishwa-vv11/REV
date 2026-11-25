export type Diagnosis = {
  status: "answered" | "abstained" | "blocked";
  confidence: number;
  checks: {
    injectionPassed: boolean;
    dtcMatch: boolean;
    groundingPassed: boolean;
    abstained: boolean;
  };
  summary: string;
  steps: {
    order: number;
    text: string;
    sourceIds: string[];
    laborHours?: number;
  }[];
  safetyNotes: string[];
  sources: {
    id: string;
    rank: number;
    score: number;
    chunkText: string;
    parentText: string;
  }[];
  latencyMs: number;
  chunksSearched: number;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  diagnosis?: Diagnosis;
  timestamp: number;
  streaming?: boolean;
  visibleWords?: number;
  showChecklist?: boolean;
  showMeta?: boolean;
};

export type ConversationState = {
  vehicle: string;
  messages: Message[];
  checkedSteps: Record<string, boolean>; // key format: `${messageId}_step_${order}`
  theme: "light" | "dark";
};
