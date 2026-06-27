"""O.M.A.-C.O.R.E. Evidence Schema
Evidence is the bridge between observation and judgment.
Evidence always belongs to exactly one hypothesis and exists
only relative to that hypothesis.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum


class EvidenceDirection(Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


class EvidenceStatus(Enum):
    COLLECTED = "collected"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


EVIDENCE_VALID_TRANSITIONS = {
    EvidenceStatus.COLLECTED: [EvidenceStatus.ACTIVE, EvidenceStatus.EXPIRED],
    EvidenceStatus.ACTIVE: [EvidenceStatus.EXPIRED, EvidenceStatus.SUPERSEDED],
    EvidenceStatus.EXPIRED: [],
    EvidenceStatus.SUPERSEDED: [],
}


@dataclass
class Evidence:
    id: str
    hypothesis_id: str
    direction: EvidenceDirection
    weight: float
    content: str
    source_id: str
    source_reliability: float
    collected_at: datetime
    independence_score: float
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    superseded_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "direction": self.direction.value,
            "weight": self.weight,
            "content": self.content,
            "source_id": self.source_id,
            "source_reliability": self.source_reliability,
            "collected_at": self.collected_at.isoformat(),
            "independence_score": self.independence_score,
            "status": self.status.value,
            "superseded_by": self.superseded_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            id=data["id"],
            hypothesis_id=data["hypothesis_id"],
            direction=EvidenceDirection(data["direction"]),
            weight=data["weight"],
            content=data["content"],
            source_id=data["source_id"],
            source_reliability=data["source_reliability"],
            collected_at=datetime.fromisoformat(data["collected_at"]),
            independence_score=data["independence_score"],
            status=EvidenceStatus(data.get("status", "collected")),
            superseded_by=data.get("superseded_by"),
        )


EVIDENCE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    weight REAL NOT NULL,
    content TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_reliability REAL NOT NULL DEFAULT 1.0,
    collected_at TEXT NOT NULL,
    independence_score REAL NOT NULL DEFAULT 0.5,
    status TEXT NOT NULL DEFAULT 'collected',
    superseded_by TEXT,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);
CREATE INDEX IF NOT EXISTS idx_evidence_hypothesis ON evidence(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_evidence_direction ON evidence(direction);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence(status);
"""
