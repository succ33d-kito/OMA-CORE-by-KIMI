"""O.M.A.-C.O.R.E. Criterion Delta Schema
A Criterion Delta is a proposed change to evaluation criteria
based on accumulated evidence. Every delta, whether applied or
rejected, is recorded for audit and outcome tracking.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class DeltaStatus(Enum):
    PENDING_REVIEW = "pending_review"
    APPLIED = "applied"
    REJECTED = "rejected"


VALID_TRANSITIONS = {
    DeltaStatus.PENDING_REVIEW: [DeltaStatus.APPLIED, DeltaStatus.REJECTED],
    DeltaStatus.APPLIED: [],
    DeltaStatus.REJECTED: [],
}


@dataclass
class CriterionDelta:
    id: str
    proposed_by: str
    source_evidence: Dict[str, List[str]]
    dimension: str
    change: str
    confidence: float
    status: DeltaStatus
    created_at: datetime
    applied_at: Optional[datetime] = None
    outcome_tracking: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "proposed_by": self.proposed_by,
            "source_evidence": json.dumps(self.source_evidence),
            "dimension": self.dimension,
            "change": self.change,
            "confidence": self.confidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "outcome_tracking": json.dumps(self.outcome_tracking) if self.outcome_tracking else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriterionDelta":
        return cls(
            id=data["id"],
            proposed_by=data["proposed_by"],
            source_evidence=json.loads(data["source_evidence"]) if isinstance(data["source_evidence"], str) else data["source_evidence"],
            dimension=data["dimension"],
            change=data["change"],
            confidence=data["confidence"],
            status=DeltaStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            applied_at=datetime.fromisoformat(data["applied_at"]) if data.get("applied_at") else None,
            outcome_tracking=json.loads(data["outcome_tracking"]) if isinstance(data.get("outcome_tracking"), str) else data.get("outcome_tracking"),
        )


CRITERION_DELTA_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS criterion_deltas (
    id TEXT PRIMARY KEY,
    proposed_by TEXT NOT NULL,
    source_evidence TEXT NOT NULL DEFAULT '{}',
    dimension TEXT NOT NULL,
    change TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    applied_at TEXT,
    outcome_tracking TEXT
);
CREATE INDEX IF NOT EXISTS idx_criterion_deltas_dimension ON criterion_deltas(dimension);
CREATE INDEX IF NOT EXISTS idx_criterion_deltas_status ON criterion_deltas(status);
CREATE INDEX IF NOT EXISTS idx_criterion_deltas_created ON criterion_deltas(created_at);
"""
