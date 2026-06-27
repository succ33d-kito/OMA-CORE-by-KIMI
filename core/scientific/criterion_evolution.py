"""O.M.A.-C.O.R.E. Criterion Evolution Logic

Criterion is emergent — it cannot be built, stored, or computed
directly. This module provides instruments to observe Criterion
development: metrics, delta proposals, and trend tracking.

Criterion deltas are NEVER auto-applied. Human review is always
required (per ARCHITECTURE V2 Invariant 1).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from core.schemas.criterion_delta_schema import (
    CriterionDelta, DeltaStatus, VALID_TRANSITIONS as DELTA_VALID_TRANSITIONS,
)
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.outcome_comparison_schema import OutcomeComparison, Verdict, ErrorType
from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus


VALID_DIMENSIONS = {
    "hypothesis_quality", "evidence_quality", "decision_quality",
    "calibration", "error_recurrence", "knowledge_yield",
    "learning_velocity", "scarce_resource_conversion",
}


def propose_delta(
    knowledge_ids: List[str],
    hypothesis_ids: List[str],
    outcome_ids: List[str],
    dimension: str,
    change: str,
    confidence: float = 0.5,
    proposed_by: str = "Scientific Laboratory",
) -> CriterionDelta:
    """Propose a CriterionDelta. Always starts at PENDING_REVIEW.

    Validates dimension against the known set of Criterion dimensions.
    Raises ValueError if dimension is unrecognized.
    """
    if dimension not in VALID_DIMENSIONS:
        raise ValueError(
            f"Invalid dimension '{dimension}'. "
            f"Valid: {sorted(VALID_DIMENSIONS)}"
        )

    return CriterionDelta(
        id=str(uuid.uuid4()),
        proposed_by=proposed_by,
        source_evidence={
            "knowledge_ids": knowledge_ids,
            "hypothesis_ids": hypothesis_ids,
            "outcome_ids": outcome_ids,
        },
        dimension=dimension,
        change=change,
        confidence=max(0.0, min(1.0, confidence)),
        status=DeltaStatus.PENDING_REVIEW,
        created_at=datetime.now(timezone.utc),
    )


def apply_delta(delta: CriterionDelta) -> CriterionDelta:
    """Transition PENDING_REVIEW → APPLIED.

    This function exists for the human reviewer to record
    their decision. It is NEVER called automatically.
    """
    allowed = DELTA_VALID_TRANSITIONS.get(delta.status, [])
    if DeltaStatus.APPLIED not in allowed:
        raise ValueError(
            f"Cannot apply delta {delta.id} from {delta.status.value}. "
            f"Only PENDING_REVIEW deltas can be applied."
        )
    delta.status = DeltaStatus.APPLIED
    delta.applied_at = datetime.now(timezone.utc)
    return delta


def reject_delta(delta: CriterionDelta) -> CriterionDelta:
    """Transition PENDING_REVIEW → REJECTED."""
    allowed = DELTA_VALID_TRANSITIONS.get(delta.status, [])
    if DeltaStatus.REJECTED not in allowed:
        raise ValueError(
            f"Cannot reject delta {delta.id} from {delta.status.value}. "
            f"Only PENDING_REVIEW deltas can be rejected."
        )
    delta.status = DeltaStatus.REJECTED
    return delta


def compute_criterion_metrics(
    hypotheses: List[Hypothesis],
    comparisons: List[OutcomeComparison],
    knowledge_list: List[Knowledge],
) -> Dict[str, Any]:
    """Compute current Criterion metrics from available data.

    All metrics are read-only observations. They do not modify
    any objects or trigger any actions.

    Returns a dict with dimension names and their computed values.
    """
    total_h = len(hypotheses)
    evaluated_h = [h for h in hypotheses if h.status == HypothesisStatus.EVALUATED]
    total_c = len(comparisons)
    confirmed = [c for c in comparisons if c.verdict == Verdict.CONFIRMED]
    rejected = [c for c in comparisons if c.verdict == Verdict.REJECTED]
    inconclusive = [c for c in comparisons if c.verdict == Verdict.INCONCLUSIVE]

    confirmation_rate = len(confirmed) / total_c if total_c > 0 else 0.0
    rejection_rate = len(rejected) / total_c if total_c > 0 else 0.0

    error_types = {}
    for c in comparisons:
        if c.error_type:
            et = c.error_type.value
            error_types[et] = error_types.get(et, 0) + 1

    dominant_error = max(error_types, key=error_types.get) if error_types else None
    dominant_error_pct = (
        error_types[dominant_error] / len(rejected) if rejected and dominant_error else 0.0
    )

    total_k = len(knowledge_list)
    validated_k = [
        k for k in knowledge_list if k.status == KnowledgeStatus.VALIDATED
    ]
    knowledge_per_outcome = total_k / total_c if total_c > 0 else 0.0
    validation_rate = len(validated_k) / total_k if total_k > 0 else 0.0

    return {
        "hypothesis_quality": {
            "total_hypotheses": total_h,
            "evaluated_hypotheses": len(evaluated_h),
            "evaluation_rate": len(evaluated_h) / total_h if total_h > 0 else 0.0,
        },
        "calibration": {
            "total_comparisons": total_c,
            "confirmation_rate": round(confirmation_rate, 4),
            "rejection_rate": round(rejection_rate, 4),
            "inconclusive_rate": len(inconclusive) / total_c if total_c > 0 else 0.0,
        },
        "error_recurrence": {
            "error_distribution": error_types,
            "dominant_error": dominant_error,
            "dominant_error_pct": round(dominant_error_pct, 4),
            "total_errors": len(error_types),
        },
        "knowledge_yield": {
            "total_knowledge": total_k,
            "validated_knowledge": len(validated_k),
            "knowledge_per_outcome": round(knowledge_per_outcome, 4),
            "validation_rate": round(validation_rate, 4),
        },
    }
