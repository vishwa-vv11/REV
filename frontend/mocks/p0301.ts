import { Diagnosis } from "../types";

export const mockP0301: Diagnosis = {
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
};
