"""O.M.A.-C.O.R.E. Knowledge Lifecycle State Machine

Lifecycle states:
  EXTRACTED → PROVISIONAL → VALIDATED / REVISED / INVALIDATED → ARCHIVED

Knowledge is the output of the learning cycle — a generalizable
lesson extracted from comparing an outcome to a hypothesis.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from core.schemas.knowledge_schema import (
    Knowledge,
    KnowledgeStatus,
    VALID_TRANSITIONS,
)
from core.schemas.outcome_comparison_schema import OutcomeComparison


def transition_knowledge(
    knowledge: Knowledge,
    target_status: KnowledgeStatus,
    reason: Optional[str] = None,
) -> Knowledge:
    """Transition knowledge to a new status.

    Validates against VALID_TRANSITIONS. Records the transition
    in revision_history. Updates updated_at.

    Raises ValueError if the transition is invalid.
    """
    allowed = VALID_TRANSITIONS.get(knowledge.status, [])
    if target_status not in allowed:
        raise ValueError(
            f"Cannot transition knowledge {knowledge.id} from "
            f"{knowledge.status.value} to {target_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    now = datetime.now(timezone.utc)
    entry = {
        "type": "status_transition",
        "from_status": knowledge.status.value,
        "to_status": target_status.value,
        "timestamp": now.isoformat(),
        "reason": reason or f"Transitioned to {target_status.value}",
    }

    knowledge.status = target_status
    knowledge.updated_at = now
    knowledge.revision_history.append(entry)

    if target_status == KnowledgeStatus.VALIDATED:
        knowledge.last_validated_at = now

    return knowledge


def can_transition(
    knowledge: Knowledge, target_status: KnowledgeStatus
) -> bool:
    """Check whether the given transition is valid without performing it."""
    return target_status in VALID_TRANSITIONS.get(knowledge.status, [])


def get_valid_transitions(knowledge: Knowledge) -> list[KnowledgeStatus]:
    """Return the list of valid target states from the current state."""
    return list(VALID_TRANSITIONS.get(knowledge.status, []))


def extract_knowledge(
    statement: str,
    hypothesis_ids: List[str],
    outcome_ids: List[str],
    evidence_summary: str,
    conditions: str,
    scope: str,
    time_horizon: str,
    confidence: float = 0.3,
    missed_opportunity_ids: Optional[List[str]] = None,
) -> Knowledge:
    """Create a new Knowledge item in EXTRACTED status.

    Knowledge always starts at EXTRACTED regardless of how confident
    the source hypothesis was. Single-outcome knowledge starts
    SPECULATIVE (confidence 0.0-0.3) until replicated.
    """
    now = datetime.now(timezone.utc)
    return Knowledge(
        id=str(uuid.uuid4()),
        statement=statement,
        hypothesis_ids=hypothesis_ids,
        outcome_ids=outcome_ids,
        missed_opportunity_ids=missed_opportunity_ids or [],
        evidence_summary=evidence_summary,
        confidence=max(0.0, min(1.0, confidence)),
        conditions=conditions,
        scope=scope,
        time_horizon=time_horizon,
        replication_count=0,
        replication_conditions=[],
        contrary_evidence_count=0,
        status=KnowledgeStatus.EXTRACTED,
        created_at=now,
        updated_at=now,
        provenance={
            "source": "manual_cli",
            "hypothesis_ids": hypothesis_ids,
            "outcome_ids": outcome_ids,
        },
        revision_history=[],
    )


def extract_from_comparison(
    comparison: OutcomeComparison,
    statement: str,
    conditions: str,
    scope: str,
    time_horizon: str,
    confidence: float = 0.3,
) -> Knowledge:
    """Create a Knowledge item from an OutcomeComparison.

    Automatically populates hypothesis_ids and outcome_ids
    from the comparison record.
    """
    return extract_knowledge(
        statement=statement,
        hypothesis_ids=[comparison.hypothesis_id],
        outcome_ids=[comparison.id],
        evidence_summary=comparison.actual_outcome,
        conditions=conditions,
        scope=scope,
        time_horizon=time_horizon,
        confidence=confidence,
    )


def promote_to_provisional(
    knowledge: Knowledge, reason: Optional[str] = None
) -> Knowledge:
    """Transition EXTRACTED → PROVISIONAL."""
    return transition_knowledge(
        knowledge, KnowledgeStatus.PROVISIONAL,
        reason=reason or "Manual review confirmed extraction"
    )


def validate_knowledge(
    knowledge: Knowledge, reason: Optional[str] = None
) -> Knowledge:
    """Transition PROVISIONAL → VALIDATED."""
    return transition_knowledge(
        knowledge, KnowledgeStatus.VALIDATED,
        reason=reason or "Sufficient replication evidence"
    )


def invalidate_knowledge(
    knowledge: Knowledge, reason: Optional[str] = None
) -> Knowledge:
    """Transition to INVALIDATED from PROVISIONAL, VALIDATED, or REVISED."""
    return transition_knowledge(
        knowledge, KnowledgeStatus.INVALIDATED,
        reason=reason or "Contradicted by new evidence"
    )


def revise_knowledge(
    knowledge: Knowledge,
    new_statement: str,
    reason: Optional[str] = None,
) -> Knowledge:
    """Transition to REVISED with an updated statement.

    Preserves the previous statement in revision_history.
    """
    prev_statement = knowledge.statement
    result = transition_knowledge(
        knowledge, KnowledgeStatus.REVISED,
        reason=reason or "Refined with new evidence"
    )
    result.statement = new_statement
    result.revision_history.append({
        "type": "statement_revision",
        "previous_statement": prev_statement,
        "new_statement": new_statement,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": reason or "Refined with new evidence",
    })
    return result


def archive_knowledge(
    knowledge: Knowledge, reason: Optional[str] = None
) -> Knowledge:
    """Transition to ARCHIVED from any status."""
    return transition_knowledge(
        knowledge, KnowledgeStatus.ARCHIVED,
        reason=reason or "Knowledge archived"
    )


def decay_confidence(
    knowledge: Knowledge,
    days_since_last_confirmation: int,
) -> float:
    """Apply the decay function to knowledge confidence.

    Formula (from spec §9):
      decay_factor = max(0.1, 1.0 - (days_since_last_confirmation / confirmation_window))
      confirmed_confidence = base_confidence * decay_factor

    Where confirmation_window starts at 180 days and extends
    by 30 days per replication.
    """
    confirmation_window = 180 + (knowledge.replication_count * 30)
    decay_factor = max(0.1, 1.0 - (days_since_last_confirmation / confirmation_window))
    adjusted = knowledge.confidence * decay_factor
    return max(0.0, min(1.0, adjusted))
