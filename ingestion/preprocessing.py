"""
Preprocessing and Document Synthesis Module for AutoDiagnose
Cleans raw relational data and synthesizes cohesive, prose-rich diagnostic
documents ready for chunking and semantic vector embedding.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.document_loader import DocumentLoader
from ingestion.metadata import DocumentMetadata, AutomotiveDocument

def format_steps(raw_steps: str) -> str:
    """Converts raw dot/bullet delimited step strings into clean numbered markdown steps."""
    if not isinstance(raw_steps, str) or not raw_steps.strip():
        return "No specific step-by-step instructions provided."
    
    # Split by bullet symbol '•'
    parts = [p.strip() for p in raw_steps.split("•") if p.strip()]
    if not parts:
        return raw_steps.strip()

    formatted_lines = []
    for i, step in enumerate(parts, 1):
        # Remove any leading numbers like '1.', '2.' if present
        clean_step = re.sub(r"^\d+[\.\)]\s*", "", step)
        formatted_lines.append(f"{i}. {clean_step}")
    return "\n".join(formatted_lines)

class DataPreprocessor:
    def __init__(self):
        self.loader = DocumentLoader()

    def process_and_synthesize(self) -> List[AutomotiveDocument]:
        """
        Executes full relational joining, cleaning, and synthesis of
        structured documents from MechanicDB.
        """
        print("[*] Loading raw datasets...")
        dtc_df = self.loader.load_dtc_codes()
        fixes_df = self.loader.load_diagnostic_fixes()
        parts_df = self.loader.load_replacement_parts()

        # Map parts to fix_id
        parts_by_fix: Dict[int, List[str]] = {}
        for _, row in parts_df.iterrows():
            f_id = int(row["fix_id"])
            p_name = str(row["part_name"])
            parts_by_fix.setdefault(f_id, []).append(p_name)

        # Map fixes to code_id
        fixes_by_code: Dict[int, List[Dict[str, Any]]] = {}
        for _, row in fixes_df.iterrows():
            c_id = int(row["code_id"])
            f_dict = row.to_dict()
            f_id = int(row["fix_id"])
            f_dict["parts_list"] = parts_by_fix.get(f_id, [])
            fixes_by_code.setdefault(c_id, []).append(f_dict)

        synthesized_docs: List[AutomotiveDocument] = []

        print("[*] Synthesizing comprehensive DTC Diagnostic Guides (Parent Documents)...")
        # 1. Generate Parent DTC Overview Guides
        for _, dtc_row in dtc_df.iterrows():
            code_id = int(dtc_row["code_id"])
            dtc_code = str(dtc_row["dtc_code"])
            category = str(dtc_row["system_category"])
            is_oem = bool(dtc_row["is_oem_specific"])
            oem_make = str(dtc_row["oem_make"])
            fault_family = str(dtc_row["fault_family"])
            short_desc = str(dtc_row["short_description"])
            explanation = str(dtc_row["detailed_technical_explanation"])

            fixes = fixes_by_code.get(code_id, [])
            # Sort fixes by probability_rank
            fixes.sort(key=lambda x: x.get("probability_rank", 99))

            # Synthesize cohesive diagnostic article
            lines = [
                f"# Diagnostic Guide: {dtc_code} - {short_desc}",
                f"**System Category:** {category} | **Fault Family:** {fault_family}",
                f"**Vehicle Application:** {'Generic OBD-II Standard' if not is_oem else f'{oem_make} Specific'}",
                "",
                "## Technical Overview & Fault Condition",
                explanation,
                "",
                "## Prioritized Troubleshooting & Repair Procedures",
            ]

            all_parts = set()
            min_costs = []
            max_costs = []
            labor_hours_list = []
            difficulty_levels = set()

            for f in fixes:
                rank = f.get("probability_rank", "-")
                title = f.get("fix_title", "Procedure")
                diff = f.get("difficulty_level", "Unknown")
                difficulty_levels.add(diff)
                
                parts_min = f.get("est_parts_cost_min_usd")
                parts_max = f.get("est_parts_cost_max_usd")
                if pd.notna(parts_min): min_costs.append(float(parts_min))
                if pd.notna(parts_max): max_costs.append(float(parts_max))

                labor = f.get("est_labor_hours")
                labor_str = f"{labor:.1f} hrs" if pd.notna(labor) else "Not specified"
                if pd.notna(labor): labor_hours_list.append(float(labor))

                cost_str = f"${parts_min:.2f} - ${parts_max:.2f}" if (pd.notna(parts_min) and pd.notna(parts_max)) else "N/A"
                steps_formatted = format_steps(f.get("step_by_step_instructions", ""))
                parts_list = f.get("parts_list", [])
                for p in parts_list:
                    all_parts.add(p)

                parts_formatted = ", ".join(parts_list) if parts_list else "None specified (or standard diagnostic tools)"

                lines.extend([
                    f"### Procedure {rank}: {title}",
                    f"- **Difficulty:** {diff} | **Estimated Labor:** {labor_str} | **Estimated Parts Cost:** {cost_str}",
                    f"- **Required Parts & Tools:** {parts_formatted}",
                    "- **Instructions:**",
                    steps_formatted,
                    ""
                ])

            content = "\n".join(lines)
            doc_id = f"dtc_guide_{code_id}_{dtc_code}"
            
            meta = DocumentMetadata(
                doc_id=doc_id,
                doc_type="dtc_overview",
                code_id=code_id,
                dtc_code=dtc_code,
                system_category=category,
                is_oem_specific=is_oem,
                oem_make=oem_make,
                fault_family=fault_family,
                short_description=short_desc,
                difficulty_level="/".join(sorted(difficulty_levels)) if difficulty_levels else None,
                est_parts_cost_min_usd=min(min_costs) if min_costs else None,
                est_parts_cost_max_usd=max(max_costs) if max_costs else None,
                est_labor_hours=sum(labor_hours_list) if labor_hours_list else None,
                parts_list=sorted(list(all_parts)),
                source_file="dtc_codes.csv + diagnostic_fixes.csv"
            )

            synthesized_docs.append(AutomotiveDocument(
                doc_id=doc_id,
                title=f"{dtc_code}: {short_desc}",
                content=content,
                metadata=meta
            ))

        # 2. Generate Granular Fix Documents (for high-precision retrieval)
        print("[*] Synthesizing granular Fix Documents...")
        for _, fix_row in fixes_df.iterrows():
            fix_id = int(fix_row["fix_id"])
            code_id = int(fix_row["code_id"])
            dtc_matches = dtc_df[dtc_df["code_id"] == code_id]
            if dtc_matches.empty:
                continue
            dtc_row = dtc_matches.iloc[0]
            dtc_code = str(dtc_row["dtc_code"])
            short_desc = str(dtc_row["short_description"])
            category = str(dtc_row["system_category"])
            is_oem = bool(dtc_row["is_oem_specific"])
            oem_make = str(dtc_row["oem_make"])
            fault_family = str(dtc_row["fault_family"])

            fix_title = str(fix_row["fix_title"])
            rank = int(fix_row["probability_rank"])
            difficulty = str(fix_row["difficulty_level"])
            parts_min = float(fix_row["est_parts_cost_min_usd"]) if pd.notna(fix_row["est_parts_cost_min_usd"]) else None
            parts_max = float(fix_row["est_parts_cost_max_usd"]) if pd.notna(fix_row["est_parts_cost_max_usd"]) else None
            labor = float(fix_row["est_labor_hours"]) if pd.notna(fix_row["est_labor_hours"]) else None
            labor_str = f"{labor:.1f} hrs" if labor is not None else "Not specified"
            cost_str = f"${parts_min:.2f} - ${parts_max:.2f}" if (parts_min and parts_max) else "N/A"
            parts_list = parts_by_fix.get(fix_id, [])
            parts_formatted = ", ".join(parts_list) if parts_list else "None specified (or standard diagnostic tools)"
            steps_formatted = format_steps(str(fix_row["step_by_step_instructions"]))

            fix_content = "\n".join([
                f"# Troubleshooting Procedure: {fix_title}",
                f"**Associated DTC:** {dtc_code} ({short_desc})",
                f"**System Category:** {category} | **Fault Family:** {fault_family}",
                f"**Vehicle Application:** {'Generic OBD-II Standard' if not is_oem else f'{oem_make} Specific'}",
                f"**Sequence Order:** Priority {rank} | **Difficulty:** {difficulty}",
                f"**Estimated Labor:** {labor_str} | **Estimated Parts Cost:** {cost_str}",
                f"**Required Parts & Tools:** {parts_formatted}",
                "",
                "## Step-by-Step Procedure",
                steps_formatted,
                "",
                "## Context & Diagnostic Advice",
                f"This procedure addresses diagnostic trouble code {dtc_code}. Follow safety protocols and verify fix using scan tool readiness checks."
            ])

            doc_id = f"fix_{fix_id}_{dtc_code}"
            meta = DocumentMetadata(
                doc_id=doc_id,
                doc_type="diagnostic_fix",
                code_id=code_id,
                dtc_code=dtc_code,
                system_category=category,
                is_oem_specific=is_oem,
                oem_make=oem_make,
                fault_family=fault_family,
                short_description=short_desc,
                fix_id=fix_id,
                fix_title=fix_title,
                probability_rank=rank,
                difficulty_level=difficulty,
                est_parts_cost_min_usd=parts_min,
                est_parts_cost_max_usd=parts_max,
                est_labor_hours=labor,
                parts_list=parts_list,
                source_file="diagnostic_fixes.csv"
            )

            synthesized_docs.append(AutomotiveDocument(
                doc_id=doc_id,
                title=f"{dtc_code} Fix: {fix_title}",
                content=fix_content,
                metadata=meta
            ))

        print(f"[+] Total synthesized documents: {len(synthesized_docs)}")
        return synthesized_docs

    def save_documents(self, docs: List[AutomotiveDocument], output_path: Path = config.SYNTHESIZED_DOCS_JSONL):
        """Saves documents to JSONL format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")
        print(f"[+] Successfully serialized {len(docs)} documents to {output_path}")

def run_preprocessing():
    print("=" * 70)
    print("STEP 1: DATA PREPROCESSING & DOCUMENT SYNTHESIS")
    print("=" * 70)
    preprocessor = DataPreprocessor()
    docs = preprocessor.process_and_synthesize()
    preprocessor.save_documents(docs)

    # Inspect intermediate sample
    print("\n[+] SAMPLE SYNTHESIZED DOCUMENT:")
    sample = docs[0]
    print(f"  * ID:    {sample.doc_id}")
    print(f"  * Title: {sample.title}")
    print(f"  * Metadata:")
    for k, v in sample.metadata.to_dict().items():
        if v:
            print(f"      {k}: {v}")
    print("\n  * Content Preview (first 400 chars):")
    print("  " + "\n  ".join(sample.content[:400].splitlines()))
    print("=" * 70)

if __name__ == "__main__":
    run_preprocessing()
