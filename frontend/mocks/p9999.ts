import { Diagnosis } from "../types";

export const mockP9999: Diagnosis = {
  status: "abstained",
  confidence: 0.05,
  checks: {
    injectionPassed: true,
    dtcMatch: false,
    groundingPassed: false,
    abstained: true,
  },
  summary:
    "No valid data found. The technical knowledge base was searched across 2,369 indexed documents, but no verified service documentation exists for trouble code P9999 or the specified condition.",
  steps: [],
  safetyNotes: [
    "Do not execute experimental or unverified mechanical procedures without certified OEM service documentation.",
  ],
  sources: [],
  latencyMs: 18,
  chunksSearched: 2369,
};
