"""
AutoDiagnose Metadata Schema Enforcement
Defines metadata schemas and validation helpers for document objects.
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

@dataclass
class DocumentMetadata:
    doc_id: str
    doc_type: str  # "dtc_overview" | "diagnostic_fix" | "technical_guide"
    code_id: int
    dtc_code: str
    system_category: str
    is_oem_specific: bool
    oem_make: str
    fault_family: str
    short_description: str
    fix_id: Optional[int] = None
    fix_title: Optional[str] = None
    probability_rank: Optional[int] = None
    difficulty_level: Optional[str] = None
    est_parts_cost_min_usd: Optional[float] = None
    est_parts_cost_max_usd: Optional[float] = None
    est_labor_hours: Optional[float] = None
    parts_list: List[str] = field(default_factory=list)
    source_file: str = "MechanicDB"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentMetadata":
        return cls(**data)

@dataclass
class AutomotiveDocument:
    doc_id: str
    title: str
    content: str
    metadata: DocumentMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomotiveDocument":
        meta = DocumentMetadata.from_dict(data["metadata"])
        return cls(
            doc_id=data["doc_id"],
            title=data["title"],
            content=data["content"],
            metadata=meta,
        )
