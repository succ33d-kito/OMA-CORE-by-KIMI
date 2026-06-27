"""O.M.A.-C.O.R.E. Knowledge Schema
Knowledge is a generalizable lesson extracted from comparing an
outcome to a hypothesis. It represents validated learning that
survived testing and replication.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class KnowledgeStatus(Enum):
    EXTRACTED = "extracted"
    PROVISIONAL = "provisional"
    VALIDATED = "validated"
    REVISED = "revised"
    INVALIDATED = "invalidated"
    ARCHIVED = "archived"


VALID_TRANSITIONS = {
    KnowledgeStatus.EXTRACTED: [KnowledgeStatus.PROVISIONAL, KnowledgeStatus.ARCHIVED],
    KnowledgeStatus.PROVISIONAL: [KnowledgeStatus.VALIDATED, KnowledgeStatus.REVISED, KnowledgeStatus.INVALIDATED, KnowledgeStatus.ARCHIVED],
    KnowledgeStatus.VALIDATED: [KnowledgeStatus.REVISED, KnowledgeStatus.INVALIDATED, KnowledgeStatus.ARCHIVED],
    KnowledgeStatus.REVISED: [KnowledgeStatus.VALIDATED, KnowledgeStatus.INVALIDATED, KnowledgeStatus.ARCHIVED],
    KnowledgeStatus.INVALIDATED: [KnowledgeStatus.ARCHIVED],
    KnowledgeStatus.ARCHIVED: [],
}


@dataclass
class Knowledge:
    id: str
    statement: str
    hypothesis_ids: List[str]
    outcome_ids: List[str]
    evidence_summary: str
    confidence: float
    conditions: str
    scope: str
    time_horizon: str
    status: KnowledgeStatus
    created_at: datetime
    updated_at: datetime
    missed_opportunity_ids: List[str] = field(default_factory=list)
    replication_count: int = 0
    replication_conditions: List[Dict[str, Any]] = field(default_factory=list)
    contrary_evidence_count: int = 0
    last_validated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    revision_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "hypothesis_ids": json.dumps(self.hypothesis_ids),
            "outcome_ids": json.dumps(self.outcome_ids),
            "missed_opportunity_ids": json.dumps(self.missed_opportunity_ids),
            "evidence_summary": self.evidence_summary,
            "confidence": self.confidence,
            "conditions": self.conditions,
            "scope": self.scope,
            "time_horizon": self.time_horizon,
            "replication_count": self.replication_count,
            "replication_conditions": json.dumps(self.replication_conditions),
            "contrary_evidence_count": self.contrary_evidence_count,
            "last_validated_at": self.last_validated_at.isoformat() if self.last_validated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "provenance": json.dumps(self.provenance),
            "revision_history": json.dumps(self.revision_history),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Knowledge":
        return cls(
            id=data["id"],
            statement=data["statement"],
            hypothesis_ids=json.loads(data["hypothesis_ids"]) if isinstance(data["hypothesis_ids"], str) else data["hypothesis_ids"],
            outcome_ids=json.loads(data["outcome_ids"]) if isinstance(data["outcome_ids"], str) else data["outcome_ids"],
            missed_opportunity_ids=json.loads(data["missed_opportunity_ids"]) if isinstance(data.get("missed_opportunity_ids"), str) else data.get("missed_opportunity_ids", []),
            evidence_summary=data["evidence_summary"],
            confidence=data["confidence"],
            conditions=data["conditions"],
            scope=data["scope"],
            time_horizon=data["time_horizon"],
            replication_count=data.get("replication_count", 0),
            replication_conditions=json.loads(data["replication_conditions"]) if isinstance(data.get("replication_conditions"), str) else data.get("replication_conditions", []),
            contrary_evidence_count=data.get("contrary_evidence_count", 0),
            last_validated_at=datetime.fromisoformat(data["last_validated_at"]) if data.get("last_validated_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=KnowledgeStatus(data["status"]),
            provenance=json.loads(data["provenance"]) if isinstance(data.get("provenance"), str) else data.get("provenance", {}),
            revision_history=json.loads(data["revision_history"]) if isinstance(data.get("revision_history"), str) else data.get("revision_history", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


KNOWLEDGE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    hypothesis_ids TEXT NOT NULL DEFAULT '[]',
    outcome_ids TEXT NOT NULL DEFAULT '[]',
    missed_opportunity_ids TEXT NOT NULL DEFAULT '[]',
    evidence_summary TEXT NOT NULL,
    confidence REAL NOT NULL,
    conditions TEXT NOT NULL,
    scope TEXT NOT NULL,
    time_horizon TEXT NOT NULL,
    replication_count INTEGER NOT NULL DEFAULT 0,
    replication_conditions TEXT NOT NULL DEFAULT '[]',
    contrary_evidence_count INTEGER NOT NULL DEFAULT 0,
    last_validated_at TEXT,
    expires_at TEXT,
    status TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT '{}',
    revision_history TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON knowledge(confidence);
CREATE INDEX IF NOT EXISTS idx_knowledge_created ON knowledge(created_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_expires ON knowledge(expires_at);
"""
