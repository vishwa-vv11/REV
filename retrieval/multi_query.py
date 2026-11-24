"""
Multi-Query Expansion Module for AutoDiagnose
Expands user diagnostic queries with technical acronym resolution,
symptom synonyms, and code-symptom multi-query variants.
"""
from typing import List, Set
import re

ACRONYM_EXPANSIONS = {
    "MAF": "mass air flow sensor",
    "MAP": "manifold absolute pressure",
    "O2": "oxygen sensor exhaust",
    "ECT": "engine coolant temperature sensor",
    "IAT": "intake air temperature",
    "TPS": "throttle position sensor pedal",
    "ABS": "anti-lock braking system wheel speed",
    "VVT": "variable valve timing camshaft phaser",
    "ECM": "engine control module computer",
    "PCM": "powertrain control module",
    "MIL": "check engine light malfunction indicator"
}

class MultiQueryExpander:
    """
    Expands automotive user queries into multi-query variants to enhance dense retrieval.
    """
    def expand(self, query: str) -> List[str]:
        """
        Generates 2 to 4 query variants combining original query,
        expanded acronyms, and extracted trouble codes.
        """
        queries = [query.strip()]

        # 1. Expand technical acronyms
        expanded_text = query
        words = re.findall(r"\b[A-Za-z0-9]+\b", query)
        has_expansion = False
        for w in words:
            upper = w.upper()
            if upper in ACRONYM_EXPANSIONS:
                expanded_text = re.sub(rf"\b{w}\b", f"{w} ({ACRONYM_EXPANSIONS[upper]})", expanded_text, flags=re.IGNORECASE)
                has_expansion = True

        if has_expansion and expanded_text not in queries:
            queries.append(expanded_text)

        # 2. Extract DTC codes and create code-isolated query
        codes = re.findall(r"\b[PCBU][0-3][0-9A-Fa-f]{3}\b", query.upper())
        if codes:
            code_query = " ".join(codes) + " diagnostic trouble code troubleshooting"
            if code_query not in queries:
                queries.append(code_query)

        return queries
