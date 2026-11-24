"""
Document Loader Module for AutoDiagnose
Handles ingestion of tabular data (CSV/JSON) and PDF service manuals.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF

import config

class DocumentLoader:
    def __init__(self, raw_data_dir: Path = config.RAW_DATA_DIR):
        self.raw_data_dir = raw_data_dir

    def load_dtc_codes(self) -> pd.DataFrame:
        """Loads and cleans the OBD-II DTC codes dataset."""
        df = pd.read_csv(self.raw_data_dir / "dtc_codes.csv", sep="|")
        df["dtc_code"] = df["dtc_code"].astype(str).str.strip().str.upper()
        df["oem_make"] = df["oem_make"].fillna("Generic").astype(str).str.strip()
        df["is_oem_specific"] = df["is_oem_specific"].astype(bool)
        return df

    def load_diagnostic_fixes(self) -> pd.DataFrame:
        """Loads diagnostic fixes and troubleshooting steps."""
        df = pd.read_csv(self.raw_data_dir / "diagnostic_fixes.csv", sep="|")
        df["fix_title"] = df["fix_title"].astype(str).str.strip()
        df["step_by_step_instructions"] = df["step_by_step_instructions"].astype(str).str.strip()
        return df

    def load_replacement_parts(self) -> pd.DataFrame:
        """Loads component and replacement part specifications."""
        df = pd.read_csv(self.raw_data_dir / "replacement_parts.csv", sep="|")
        df["part_name"] = df["part_name"].astype(str).str.strip()
        return df

    def load_cost_metadata(self) -> Dict[str, Any]:
        """Loads cost basis and vocabulary definitions."""
        with open(self.raw_data_dir / "cost_metadata.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def load_ordering_metadata(self) -> Dict[str, Any]:
        """Loads semantic definitions for ranking/ordering."""
        with open(self.raw_data_dir / "ordering_metadata.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def load_pdf_manual(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts text from a vehicle service manual PDF page by page.
        Returns a list of dictionaries with page numbers and text content.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF manual not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        pages_content = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            if text:
                pages_content.append({
                    "page_number": page_num + 1,
                    "content": text,
                    "source": pdf_path.name
                })
        doc.close()
        return pages_content
