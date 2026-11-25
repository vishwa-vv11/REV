# REV — Diagnostic Copilot Frontend

A lightweight, phone-first frontend for **REV**, a local RAG-based vehicle diagnostics assistant (OBD-II codes, symptoms, and grounded repair guidance with citations).

Built with **Next.js (App Router)**, **TypeScript**, **Tailwind CSS**, and **Lucide React**. Designed to work completely standalone using typed mock responses, with a one-line switch to connect to a live backend.

---

## Features

- **Phone-First Layout**: Centered phone-style frame (~420px max-width) on desktop; responsive dual-pane on wide displays (`>=1024px`) showing the full **Evidence / Source Inspector**.
- **Garage-Ready Dark & Light Modes**: High-contrast dark mode tailored for garage workstations, paired with a flat, clean light mode.
- **Interactive Repair Checklist**:
  - Semantic `<input type="checkbox">` elements.
  - Checked steps are struck through and muted with real-time completion counter (*"1 of 3 done"*).
  - State persisted automatically in `localStorage` per vehicle / conversation.
- **Inline Citation Expansion**:
  - Accessible citation buttons (`<button>`) expand source chunks inline under specific repair steps.
  - "Show parent guide" toggle reveals the complete section context from OEM manuals.
- **Grounded Safety Callouts**: Amber callouts for safety precautions before handling electrical, fuel, or ignition components.
- **Audited Abstention & Blocked States**:
  - Deliberate amber card (*"No valid data found"*) with quick actions (*"Upload OEM manual"*, *"Recheck code"*) for ungrounded or unknown DTC queries (e.g. `P9999`).
  - Neutral blocked card for out-of-scope or filtered inquiries.
- **Simulated Streaming**: Demonstrates fast local inference with retrieval metrics displayed first, followed by word-by-word streaming (~30ms per word), then checklist reveal.
- **One-Click Suggestion Chips**: Quick prompts like *"The coil swap did not help"* and *"What about P9999?"*.
- **Manual Attachment Support**: Attachment button with native PDF file picker dialog.

---

## Getting Started

### Prerequisites
- Node.js 18.x or later
- npm or pnpm

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Production Build
```bash
npm run build
npm start
```

---

## Architecture & Data Contract

All diagnostic responses adhere to the standard TypeScript contract defined in [`types.ts`](file:///e:/Vishwa/learning/RAG/frontend/types.ts):

```typescript
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
```

### Switching from Mock to Live Backend

In [`frontend/lib/api.ts`](file:///e:/Vishwa/learning/RAG/frontend/lib/api.ts), toggle `USE_MOCK`:

```typescript
// Set to false when your FastAPI or Flask RAG server is running
export const USE_MOCK = false;
export const API_BASE_URL = "http://localhost:8000";
```

The `fetchDiagnosis` function will automatically post to `${API_BASE_URL}/api/diagnose`.

---

## Accessibility (a11y)

- All icon buttons feature descriptive `aria-label` tags.
- Checklists use native `<input type="checkbox">` elements navigable via keyboard.
- Citations and toggles are interactive `<button>` elements with visible `:focus-visible` rings.
- Dynamic assistant replies announce progress cleanly with `aria-live="polite"`.
- Text sizes strictly $\ge 12\text{px}$ and tap targets $\ge 44\text{px}$.
