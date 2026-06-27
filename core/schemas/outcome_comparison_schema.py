"""O.M.A.-C.O.R.E. Outcome Comparison Schema
The Outcome Comparison is the record of comparing a hypothesis's
predicted consequence with an actual outcome. It produces a verdict,
optionally classifies error types, and triggers knowledge extraction.
Outcome comparisons are immutable once created.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum
import json


class Verdict(Enum):
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    CORRECT_BLOCK = "correct_block"
    INCORRECT_BLOCK = "incorrect_block"
    UNKNOWN = "unknown"


class ErrorType(Enum):
    WRONG_HYPOTHESIS = "wrong_hypothesis"
    WRONG_TIMING = "wrong_timing"
    POOR_EXECUTION = "poor_execution"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    EXTERNAL_SHOCK = "external_shock"
    CORRECT_DECISION_BAD_OUTCOME = "correct_decision_bad_outcome"
    BAD_DECISION_GOOD_OUTCOME = "bad_decision_good_outcome"


class ComparisonType(Enum):
    EXECUTED = "executed"
    MISSED_OPPORTUNITY = "missed_opportunity"


@dataclass
class OutcomeComparison:
    id: str
    hypothesis_id: str
    verdict: Verdict
    comparison_type: ComparisonType
    predicted_consequence: str
    actual_outcome: str
    comparison_confidence: float
    compared_at: datetime
    decision_id: Optional[str] = None
    outcome_id: Optional[str] = None
    error_type: Optional[ErrorType] = None
    error_detail: Optional[str] = None
    tolerance_applied: Optional[Dict[str, Any]] = None
    knowledge_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "decision_id": self.decision_id,
            "outcome_id": self.outcome_id,
            "verdict": self.verdict.value,
            "error_type": self.error_type.value if self.error_type else None,
            "comparison_type": self.comparison_type.value,
            "predicted_consequence": self.predicted_consequence,
            "actual_outcome": self.actual_outcome,
            "tolerance_applied": json.dumps(self.tolerance_applied) if self.tolerance_applied else None,
            "comparison_confidence": self.comparison_confidence,
            "error_detail": self.error_detail,
            "knowledge_triggered": self.knowledge_triggered,
            "compared_at": self.compared_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutcomeComparison":
        return cls(
            id=data["id"],
            hypothesis_id=data["hypothesis_id"],
            decision_id=data.get("decision_id"),
            outcome_id=data.get("outcome_id"),
            verdict=Verdict(data["verdict"]),
            error_type=ErrorType(data["error_type"]) if data.get("error_type") else None,
            comparison_type=ComparisonType(data.get("comparison_type", "executed")),
            predicted_consequence=data["predicted_consequence"],
            actual_outcome=data["actual_outcome"],
            tolerance_applied=json.loads(data["tolerance_applied"]) if data.get("tolerance_applied") else None,
            comparison_confidence=data["comparison_confidence"],
            error_detail=data.get("error_detail"),
            knowledge_triggered=data.get("knowledge_triggered", False),
            compared_at=datetime.fromisoformat(data["compared_at"]),
        )


OUTCOME_COMPARISON_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS outcome_comparisons (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    decision_id TEXT,
    outcome_id TEXT,
    verdict TEXT NOT NULL,
    error_type TEXT,
    comparison_type TEXT NOT NULL DEFAULT 'executed',
    predicted_consequence TEXT NOT NULL,
    actual_outcome TEXT NOT NULL,
    tolerance_applied TEXT,
    comparison_confidence REAL NOT NULL,
    error_detail TEXT,
    knowledge_triggered INTEGER NOT NULL DEFAULT 0,
    compared_at TEXT NOT NULL,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);
CREATE INDEX IF NOT EXISTS idx_outcome_comparisons_hypothesis ON outcome_comparisons(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_outcome_comparisons_verdict ON outcome_comparisons(verdict);
CREATE INDEX IF NOT EXISTS idx_outcome_comparisons_compared_at ON outcome_comparisons(compared_at);
"""
