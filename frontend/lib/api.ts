import { Diagnosis } from "../types";
import { mockP0301, mockP9999, mockBlocked } from "../mocks";

/**
 * Global mock flag. Set to false when connecting to the real FastAPI / Ollama backend.
 */
export const USE_MOCK = true;

/**
 * Route request to mock data based on query keywords or trouble code.
 */
export async function fetchDiagnosis(
  query: string,
  vehicle: string
): Promise<Diagnosis> {
  if (USE_MOCK) {
    const q = query.trim().toUpperCase();

    // Adversarial or safety violations
    if (
      q.includes("IGNORE") ||
      q.includes("JAILBREAK") ||
      q.includes("HOTWIRE") ||
      q.includes("BYPASS")
    ) {
      return mockBlocked;
    }

    // Negative / out-of-scope query
    if (q.includes("P9999") || q.includes("WARP") || q.includes("SPACESHIP")) {
      return mockP9999;
    }

    // Default answered diagnosis (P0301 or general symptom query)
    return mockP0301;
  }

  // Real backend integration hook (one-line activation)
  const response = await fetch("http://localhost:8000/api/diagnose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, vehicle }),
  });

  if (!response.ok) {
    throw new Error(`Diagnostic API failure: ${response.statusText}`);
  }

  return response.json();
}
