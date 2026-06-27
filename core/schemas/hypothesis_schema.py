"""O.M.A.-C.O.R.E. Hypothesis Schema
The hypothesis is the unit of learning — the smallest structure
that can be tested, can be wrong in a specific way, can produce
a generalizable lesson, and can be compared across contexts.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any
from enum import Enum
import json


class HypothesisStatus(Enum):
    FORMULATED = "formulated"
    ACTIVE = "active"
    EVALUATED = "evaluated"
    ARCHIVED = "archived"


VALID_TRANSITIONS = {
    HypothesisStatus.FORMULATED: [HypothesisStatus.ACTIVE, HypothesisStatus.ARCHIVED],
    HypothesisStatus.ACTIVE: [HypothesisStatus.EVALUATED, HypothesisStatus.ARCHIVED],
    HypothesisStatus.EVALUATED: [HypothesisStatus.ARCHIVED],
    HypothesisStatus.ARCHIVED: [],
}


@dataclass
class Hypothesis:
    id: str
    title: str
    description: str
    predicted_consequence: str
    conditions: str
    invalidation_conditions: str
    confidence: float
    status: HypothesisStatus
    created_at: datetime
    updated_at: datetime
    status_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "predicted_consequence": self.predicted_consequence,
            "conditions": self.conditions,
            "invalidation_conditions": self.invalidation_conditions,
            "confidence": self.confidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status_history": self.status_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            predicted_consequence=data["predicted_consequence"],
            conditions=data["conditions"],
            invalidation_conditions=data["invalidation_conditions"],
            confidence=data["confidence"],
            status=HypothesisStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status_history=data.get("status_history", []),
        )


HYPOTHESIS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    predicted_consequence TEXT NOT NULL,
    conditions TEXT NOT NULL,
    invalidation_conditions TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status_history TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(status);
CREATE INDEX IF NOT EXISTS idx_hypotheses_created ON hypotheses(created_at);
"""
