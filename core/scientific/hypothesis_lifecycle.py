"""O.M.A.-C.O.R.E. Hypothesis Lifecycle State Machine

Lifecycle states (simplified from 02_SCIENTIFIC_OBJECT_MODEL.md 6.1):
  FORMULATED → ACTIVE → EVALUATED → ARCHIVED

Transitions are validated. Invalid transitions raise ValueError.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from core.schemas.hypothesis_schema import (
    Hypothesis,
    HypothesisStatus,
    VALID_TRANSITIONS,
)


def transition_hypothesis(
    hypothesis: Hypothesis,
    target_status: HypothesisStatus,
    reason: Optional[str] = None,
) -> Hypothesis:
    """Transition a hypothesis to a new status.

    Validates the transition against VALID_TRANSITIONS.
    Appends the transition to status_history.
    Updates hypothesis.updated_at.

    Raises ValueError if the transition is invalid.
    """
    allowed = VALID_TRANSITIONS.get(hypothesis.status, [])
    if target_status not in allowed:
        raise ValueError(
            f"Cannot transition hypothesis {hypothesis.id} from "
            f"{hypothesis.status.value} to {target_status.value}. "
            f"Allowed transitions from {hypothesis.status.value}: "
            f"{[s.value for s in allowed]}"
        )

    now = datetime.now(timezone.utc)
    entry = {
        "from_status": hypothesis.status.value,
        "to_status": target_status.value,
        "timestamp": now.isoformat(),
        "reason": reason or f"Transitioned to {target_status.value}",
    }

    hypothesis.status = target_status
    hypothesis.updated_at = now
    hypothesis.status_history.append(entry)

    return hypothesis


def can_transition(
    hypothesis: Hypothesis, target_status: HypothesisStatus
) -> bool:
    """Check whether the given transition is valid without performing it."""
    return target_status in VALID_TRANSITIONS.get(hypothesis.status, [])


def get_valid_transitions(hypothesis: Hypothesis) -> list[HypothesisStatus]:
    """Return the list of valid target states from the current state."""
    return list(VALID_TRANSITIONS.get(hypothesis.status, []))
