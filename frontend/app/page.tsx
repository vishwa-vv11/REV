"use client";

import React, { useState, useEffect, useRef } from "react";
import { Message, Diagnosis } from "../types";
import { fetchDiagnosis } from "../lib/api";
import { Header } from "../components/Header";
import { MessageList } from "../components/MessageList";
import { SuggestionChips } from "../components/SuggestionChips";
import { InputBar } from "../components/InputBar";
import { SourcePanel } from "../components/SourcePanel";

const LOCAL_STORAGE_CHECK_KEY = "rev_checklist_state_v1";
const LOCAL_STORAGE_THEME_KEY = "rev_theme_pref_v1";
const LOCAL_STORAGE_VEHICLE_KEY = "rev_vehicle_pref_v1";

const INITIAL_MESSAGE: Message = {
  id: "msg_init_001",
  role: "assistant",
  content: "Hello! Enter an OBD-II fault code or vehicle symptom to begin troubleshooting.",
  timestamp: Date.now() - 3600000,
  showMeta: true,
  streaming: false,
  visibleWords: 999,
  showChecklist: true,
  diagnosis: {
    status: "answered",
    confidence: 0.88,
    checks: {
      injectionPassed: true,
      dtcMatch: true,
      groundingPassed: true,
      abstained: false,
    },
    summary:
      "Cylinder 1 misfire detected (P0301). The engine control module recorded combustion irregularity specifically on cylinder 1. Follow this isolated diagnostic sequence to identify if the fault stems from ignition coil breakdown, fouled spark plug gap, or fuel delivery restriction.",
    steps: [
      {
        order: 1,
        text: "Verify diagnostic trouble code and record freeze-frame telemetry (engine RPM, calculated load, short-term fuel trim).",
        sourceIds: ["dtc_sample_0101"],
        laborHours: 0.2,
      },
      {
        order: 2,
        text: "Cross-swap cylinder 1 ignition coil pack with cylinder 2. Clear fault codes, run vehicle at idle, and inspect if misfire migrates to cylinder 2 (P0302).",
        sourceIds: ["fix_sample_0142"],
        laborHours: 0.5,
      },
      {
        order: 3,
        text: "Disconnect cylinder 1 fuel injector harness connector and measure coil internal resistance using a digital multimeter (normal specification: 11.5 - 14.2 ohms at 20°C).",
        sourceIds: ["fix_sample_0189"],
        laborHours: 0.5,
      },
    ],
    safetyNotes: [
      "Turn off ignition and let engine block cool to ambient temperature before dismounting coil packs or touching spark plug boots.",
      "Do not probe injector electrical harness with oversized test leads to avoid spreading terminal tension pins.",
    ],
    sources: [
      {
        id: "dtc_sample_0101",
        rank: 1,
        score: 0.92,
        chunkText:
          "[Powertrain - Ignition & Timing] Scan tool telemetry verification for DTC P0301. Always capture freeze-frame telemetry before clearing codes. Check if misfire occurs predominantly at idle or under load.",
        parentText:
          "# Generic Vehicle Powertrain Diagnostic Reference Manual\n\n## Section 3.2: Single-Cylinder Misfire Monitor (P0301 - P0308)\nThe vehicle engine management unit monitors crankshaft rotational velocity variations between cylinder firings. When acceleration drops below the calculated threshold for cylinder 1, P0301 is logged. Priority sequence mandates electrical freeze-frame review followed by mechanical component isolation.",
      },
      {
        id: "fix_sample_0142",
        rank: 2,
        score: 0.88,
        chunkText:
          "[Step-by-step Repair] Procedure: Ignition coil isolation swap. Disengage wiring retainer clip, remove 10mm retaining bolt, and swap cylinder 1 coil with cylinder 2. Re-test for code migration.",
        parentText:
          "# Comprehensive Workshop Troubleshooting Procedures: Ignition Circuits\n\n## Coil-on-Plug (COP) Field Verification\nDirect component swapping remains the fastest non-invasive technique to prove coil degradation without laboratory oscilloscopes. If the misfire counter transitions to the partner cylinder, coil replacement is confirmed. If the misfire remains on cylinder 1, proceed directly to injector resistance testing.",
      },
      {
        id: "fix_sample_0189",
        rank: 3,
        score: 0.84,
        chunkText:
          "[Component Test] Fuel injector circuit analysis. Disconnect injector terminal plug. Set multimeter to 200 ohm scale. Measure across internal pins. Resistance out of specification requires injector replacement.",
        parentText:
          "# Port Fuel Delivery Diagnostic Standards\n\n## Fuel Injector Electrical Specifications\nSolenoid-driven high-impedance fuel injectors should demonstrate stable resistance within specified manufacturer range. Values below 10 ohms indicate shorted internal windings, while infinite resistance indicates an open internal coil circuit.",
      },
    ],
    latencyMs: 35,
    chunksSearched: 2369,
  },
};

export default function DiagnosticChatPage() {
  const [vehicle, setVehicle] = useState("2016 Civic 1.8L");
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [checkedSteps, setCheckedSteps] = useState<Record<string, boolean>>({});
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeSourceId, setActiveSourceId] = useState<string | null>("fix_sample_0142");
  const [showWidePanel, setShowWidePanel] = useState(true);

  // Load preferences from localStorage on client mount
  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem(LOCAL_STORAGE_THEME_KEY) as
        | "light"
        | "dark"
        | null;
      if (savedTheme) {
        setTheme(savedTheme);
        document.documentElement.classList.toggle("dark", savedTheme === "dark");
      } else {
        document.documentElement.classList.add("dark");
      }

      const savedVehicle = localStorage.getItem(LOCAL_STORAGE_VEHICLE_KEY);
      if (savedVehicle) setVehicle(savedVehicle);

      const savedChecks = localStorage.getItem(LOCAL_STORAGE_CHECK_KEY);
      if (savedChecks) {
        setCheckedSteps(JSON.parse(savedChecks));
      } else {
        // default step 1 checked as in spec ("1 of 3 done")
        const defaultInit = { msg_init_001_step_1: true };
        setCheckedSteps(defaultInit);
        localStorage.setItem(LOCAL_STORAGE_CHECK_KEY, JSON.stringify(defaultInit));
      }
    } catch {
      // ignore storage access errors in restricted environments
    }
  }, []);

  const handleThemeToggle = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    document.documentElement.classList.toggle("dark", nextTheme === "dark");
    try {
      localStorage.setItem(LOCAL_STORAGE_THEME_KEY, nextTheme);
    } catch {}
  };

  const handleVehicleChange = (newVehicle: string) => {
    setVehicle(newVehicle);
    try {
      localStorage.setItem(LOCAL_STORAGE_VEHICLE_KEY, newVehicle);
    } catch {}
  };

  const handleToggleStep = (stepKey: string) => {
    setCheckedSteps((prev) => {
      const updated = { ...prev, [stepKey]: !prev[stepKey] };
      try {
        localStorage.setItem(LOCAL_STORAGE_CHECK_KEY, JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  // Simulated streaming function
  const streamAssistantResponse = (
    msgId: string,
    diagnosis: Diagnosis
  ) => {
    const words = diagnosis.summary.split(" ");
    let currentWordIndex = 0;

    // Phase 1: Show metadata immediately
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId
          ? {
              ...m,
              diagnosis,
              showMeta: true,
              streaming: true,
              visibleWords: 0,
              showChecklist: false,
            }
          : m
      )
    );

    // If abstained or blocked, reveal at once
    if (diagnosis.status !== "answered") {
      setTimeout(() => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  streaming: false,
                  visibleWords: words.length,
                  showChecklist: true,
                }
              : m
          )
        );
        setIsLoading(false);
      }, 200);
      return;
    }

    // Phase 2: Word-by-word streaming (~30ms per word)
    const streamInterval = setInterval(() => {
      currentWordIndex += 1;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                visibleWords: currentWordIndex,
              }
            : m
        )
      );

      if (currentWordIndex >= words.length) {
        clearInterval(streamInterval);
        // Phase 3: Reveal checklist and safety callouts
        setTimeout(() => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    streaming: false,
                    showChecklist: true,
                  }
                : m
            )
          );
          setIsLoading(false);
        }, 150);
      }
    }, 30);
  };

  const handleSend = async (queryText?: string) => {
    const query = (queryText ?? input).trim();
    if (!query || isLoading) return;

    setInput("");
    setIsLoading(true);

    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now() + 1}`;

    const userMessage: Message = {
      id: userMsgId,
      role: "user",
      content: query,
      timestamp: Date.now(),
    };

    const pendingAssistantMessage: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: Date.now() + 1,
      showMeta: false,
      streaming: true,
      visibleWords: 0,
      showChecklist: false,
    };

    setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);

    try {
      const diag = await fetchDiagnosis(query, vehicle);
      if (diag.sources && diag.sources.length > 0) {
        setActiveSourceId(diag.sources[0].id);
      }
      streamAssistantResponse(assistantMsgId, diag);
    } catch {
      setIsLoading(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? {
                ...m,
                content: "Network error occurred while contacting diagnostic engine.",
                streaming: false,
              }
            : m
        )
      );
    }
  };

  const handlePdfAttached = (filename: string) => {
    // Acknowledge attachment without upload logic
    handleSend(`Attached OEM Service Manual: ${filename}. Please analyze with respect to ${vehicle}.`);
  };

  // Find sources across all messages for side panel
  const allCurrentSources = messages
    .flatMap((m) => m.diagnosis?.sources || [])
    .filter(
      (source, index, self) =>
        index === self.findIndex((s) => s.id === source.id)
    );

  return (
    <main className="w-full h-screen max-h-screen flex items-center justify-center p-0 sm:p-3 lg:p-4 overflow-hidden">
      {/* Outer wrapper: centered phone frame on mobile/tablet, dual pane on >=1024px */}
      <div className="w-full max-w-full lg:max-w-5xl h-full sm:h-[840px] sm:max-h-[96vh] flex flex-col lg:flex-row items-stretch justify-center gap-0 lg:gap-4 sm:rounded-[24px] overflow-hidden shadow-2xl bg-garage-100 dark:bg-garage-900 border-0 sm:border border-garage-300 dark:border-garage-800">
        
        {/* Phone Frame: Mobile-first single column (max-w ~400-420px on desktop) */}
        <div className="w-full lg:w-[420px] shrink-0 h-full flex flex-col bg-white dark:bg-garage-950 border-r-0 lg:border-r border-garage-200 dark:border-garage-800 sm:rounded-[24px] lg:rounded-r-none overflow-hidden shadow-md">
          <Header
            vehicle={vehicle}
            onVehicleChange={handleVehicleChange}
            theme={theme}
            onThemeToggle={handleThemeToggle}
          />

          <MessageList
            messages={messages}
            checkedSteps={checkedSteps}
            onToggleStep={handleToggleStep}
            onSelectSource={(id) => {
              setActiveSourceId(id);
              setShowWidePanel(true);
            }}
            onUploadManual={() => {
              const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
              fileInput?.click();
            }}
            onRecheckCode={() => {
              setInput("P0301");
            }}
            activeSourceId={activeSourceId}
          />

          {/* Suggestion Chips */}
          <div className="px-2 bg-white dark:bg-garage-950">
            <SuggestionChips
              onSelect={(text) => handleSend(text)}
              disabled={isLoading}
            />
          </div>

          {/* Input Bar */}
          <InputBar
            input={input}
            setInput={setInput}
            onSend={() => handleSend()}
            disabled={isLoading}
            onPdfAttached={handlePdfAttached}
          />
        </div>

        {/* Wide Screen Evidence Panel (>=1024px) */}
        {showWidePanel && (
          <div className="hidden lg:flex flex-1 h-full rounded-r-[24px] overflow-hidden bg-white dark:bg-garage-950">
            <SourcePanel
              sources={allCurrentSources}
              activeSourceId={activeSourceId}
              onClose={() => setShowWidePanel(false)}
            />
          </div>
        )}

      </div>
    </main>
  );
}
