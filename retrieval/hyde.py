"""
AutoDiagnose HyDE: Hypothetical Document Embeddings Module
Bridges the semantic gap between human layperson symptom descriptions
and technical OEM service manuals by using an LLM (with robust rule-based fallback)
to generate a hypothetical technical diagnostic excerpt before vector search.
"""
from typing import Optional, List
import urllib.request
import urllib.error
import json
import re
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

HYDE_PROMPT_TEMPLATE = (
    "You are an automotive master technician. A vehicle owner describes this physical symptom:\n"
    "\"{query}\"\n\n"
    "Write a brief technical OEM workshop manual troubleshooting excerpt (2 to 3 sentences) specifying:\n"
    "1. The primary mechanical or electrical fault\n"
    "2. The most probable OBD-II Diagnostic Trouble Code (e.g. P0300, P0301, P0101, P0171, P0420, C0035)\n"
    "3. Key diagnostic components to inspect (e.g. ignition coil, spark plug, MAF sensor, vacuum hose)\n\n"
    "Write ONLY the technical diagnostic excerpt. No introductory or closing remarks."
)

# High-precision fallback symptom-to-fault patterns when Ollama is offline or warming up
FALLBACK_SYMPTOM_MAP = [
    (
        r"\b(vibrat\w*|shak\w*|stumb\w*|misfir\w*|shudder\w*|sputter\w*|chug\w*)\b",
        "Combustion irregularity and cylinder misfire (DTC P0300, P0301, P0302, P0306). The fault stems from ignition coil breakdown, fouled spark plug gap, or fuel delivery restriction under acceleration load. Inspect coil pack secondary voltage and swap coils across cylinders to verify code migration."
    ),
    (
        r"\b(hesitat\w*|throttle\w*|bog\w*|jerk\w*|power\s+loss|sluggish|lag\w*)\b",
        "Mass or volume air flow sensor range/performance (DTC P0101, P0102) or throttle position sensor correlation error. Contamination on the hot-wire element causes false intake airflow metering resulting in fuel delivery starvation during acceleration tip-in."
    ),
    (
        r"\b(hiss\w*|vacuum\w*|lean\w*|whistl\w*|air\s+leak)\b",
        "System too lean bank 1 (DTC P0171, P0174). Unmetered air entering past intake manifold gasket, disconnected vacuum line, or sticking positive crankcase ventilation (PCV) valve causing high short-term fuel trim values at idle."
    ),
    (
        r"\b(sulfur|rotten\s*egg|exhaust\s*smell|cat\s*smell)\b",
        "Catalytic converter system efficiency below threshold (DTC P0420). Thermal breakdown or washcoat poisoning prevents conversion of hydrogen sulfide and hydrocarbons into carbon dioxide and water."
    ),
    (
        r"\b(gas\s*smell|fuel\s*odor|gasoline\s*smell|fuel\s*tank|fume\w*)\b",
        "Evaporative emission control system vapor leak (DTC P0442, P0455). Pressure decay test reveals deteriorated fuel filler cap gasket seal, purge valve solenoid mechanical failure, or hairline crack in charcoal canister vapor line."
    ),
    (
        r"\b(abs|traction|wheel\s*speed|brake\s*puls\w*|brake\s*light)\b",
        "Anti-lock braking system wheel speed sensor circuit failure (DTC C0031, C0035, C0040). Debris accumulation on reluctance tone ring or open wiring harness causing false wheel slip detection during braking."
    ),
    (
        r"\b(rattl\w*|timing\w*|chain\w*|camshaft\w*|crankshaft\w*|phaser\w*|vvt\w*)\b",
        "Camshaft position timing over-advanced bank 1 (DTC P0011, P0016). Variable valve timing (VVT) oil control solenoid screen sludge restriction or elongated timing chain resulting in camshaft-to-crankshaft synchronization failure."
    ),
    (
        r"\b(idle\w*|stall\w*|dying\s+at\s+stop|rpm\s+drop)\b",
        "Idle air control system RPM lower than expected (DTC P0506, P0507). Carbon buildup on electronic throttle body bore or sticking idle air bypass valve preventing steady curb idle regulation."
    )
]

class HyDEGenerator:
    """
    Generates hypothetical OEM diagnostic manual excerpts from human driver queries.
    Uses local Ollama LLM when online, with instant domain fallback when offline.
    """
    def __init__(
        self,
        ollama_host: str = config.OLLAMA_HOST,
        model_name: str = config.DEFAULT_LLM_MODEL,
        timeout_seconds: int = 4
    ):
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def generate(self, user_query: str) -> str:
        """
        Synthesizes a hypothetical OEM diagnostic document corresponding to the user symptom.
        """
        clean_query = user_query.strip()
        if not clean_query:
            return ""

        # Try LLM generation first if available
        llm_doc = self._call_ollama(clean_query)
        if llm_doc and len(llm_doc.strip()) > 30:
            return llm_doc.strip()

        # Fallback to high-precision domain ontology
        return self._rule_based_fallback(clean_query)

    def _call_ollama(self, query: str) -> Optional[str]:
        """Queries local Ollama instance with a strict timeout."""
        try:
            url = f"{self.ollama_host}/api/generate"
            prompt = HYDE_PROMPT_TEMPLATE.format(query=query)
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 120
                }
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception:
            return None

    def _rule_based_fallback(self, query: str) -> str:
        """Extracts matching mechanical fault descriptions from query keywords."""
        query_lower = query.lower()
        matched_excerpts = []

        for pattern, excerpt in FALLBACK_SYMPTOM_MAP:
            if re.search(pattern, query_lower):
                matched_excerpts.append(excerpt)

        if matched_excerpts:
            return " ".join(matched_excerpts[:2])

        # Generic default technical frame
        return (
            f"Technical powertrain diagnostics regarding reported symptom '{query}'. "
            "Inspect primary ignition circuits, air-fuel metering sensors, and electronic control actuators."
        )
