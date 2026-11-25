import { Diagnosis } from "../types";

export const mockBlocked: Diagnosis = {
  status: "blocked",
  confidence: 0.0,
  checks: {
    injectionPassed: false,
    dtcMatch: false,
    groundingPassed: false,
    abstained: false,
  },
  summary:
    "This request cannot be processed. It triggered safety boundaries regarding adversarial prompt patterns or vehicle control tampering.",
  steps: [],
  safetyNotes: [],
  sources: [],
  latencyMs: 12,
  chunksSearched: 0,
};
