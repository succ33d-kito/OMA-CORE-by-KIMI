"""O.M.A.-C.O.R.E. Evidence Lifecycle State Machine

Lifecycle states (from 02_SCIENTIFIC_OBJECT_MODEL.md 6.2):
  COLLECTED → ACTIVE → EXPIRED / SUPERSEDED

Evidence always belongs to exactly one hypothesis.
Evidence is only meaningful relative to its hypothesis.
"""
from datetime import datetime, timezone
from typing import Optional

from core.schemas.evidence_schema import (
    Evidence,
    EvidenceStatus,
    EVIDENCE_VALID_TRANSITIONS,
)
from core.schemas.hypothesis_schema import Hypothesis


def activate_evidence(evidence: Evidence) -> Evidence:
    """Transition evidence from COLLECTED to ACTIVE.

    ACTIVE evidence is contributing to hypothesis evaluation.
    """
    return _transition(evidence, EvidenceStatus.ACTIVE)


def expire_evidence(evidence: Evidence) -> Evidence:
    """Transition evidence from COLLECTED or ACTIVE to EXPIRED.

    EXPIRED evidence has passed its useful lifetime.
    """
    return _transition(evidence, EvidenceStatus.EXPIRED)


def supersede_evidence(
    evidence: Evidence, replacement_id: str
) -> Evidence:
    """Transition evidence from ACTIVE to SUPERSEDED.

    SUPERSEDED evidence has been replaced by better evidence.
    """
    result = _transition(evidence, EvidenceStatus.SUPERSEDED)
    result.superseded_by = replacement_id
    return result


def _transition(
    evidence: Evidence, target_status: EvidenceStatus
) -> Evidence:
    """Internal: validate and apply an evidence state transition."""
    allowed = EVIDENCE_VALID_TRANSITIONS.get(evidence.status, [])
    if target_status not in allowed:
        raise ValueError(
            f"Cannot transition evidence {evidence.id} from "
            f"{evidence.status.value} to {target_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )
    evidence.status = target_status
    return evidence


def get_active_evidence_count(
    hypothesis: Hypothesis, evidence_list: list[Evidence]
) -> dict:
    """Count supporting and contradicting active evidence for a hypothesis."""
    supports = 0
    contradicts = 0
    for e in evidence_list:
        if e.hypothesis_id == hypothesis.id and e.status == EvidenceStatus.ACTIVE:
            if e.direction.value == "supports":
                supports += 1
            else:
                contradicts += 1
    return {"supports": supports, "contradicts": contradicts}
