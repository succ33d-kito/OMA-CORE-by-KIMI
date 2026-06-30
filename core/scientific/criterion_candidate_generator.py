"""criterion_candidate_generator.py — Outcome patterns → CriterionDelta candidates.

Generates PENDING_REVIEW criterion deltas from outcome patterns.
Never applies changes to operational criteria.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.schemas.outcome_comparison_schema import Verdict
from core.scientific.scientific_store import ScientificStore
from core.scientific.criterion_evolution import VALID_DIMENSIONS


PATTERN_DIMENSION_MAP = {
    "high_accuracy_confirm": "calibration",
    "low_accuracy_reject": "calibration",
    "high_inconclusive": "decision_quality",
    "rejection_dominated": "hypothesis_quality",
    "high_confirmed_rejected_ratio": "knowledge_yield",
    "low_confirmed_rejected_ratio": "hypothesis_quality",
}


class CriterionCandidateGenerator:
    """Generate criterion delta candidates from outcome patterns."""

    def __init__(self, scientific_db: str = "scientific.db"):
        self.store = ScientificStore(scientific_db)

    def analyze_recent_outcomes(self, limit: int = 100) -> Dict[str, Any]:
        comparisons = self.store.list_outcome_comparisons(limit=limit)
        if not comparisons:
            return {
                "total_analyzed": 0,
                "patterns": {},
                "recommended_deltas": [],
            }

        total = len(comparisons)
        confirmed = sum(1 for c in comparisons if c.verdict == Verdict.CONFIRMED)
        partial = sum(1 for c in comparisons if c.verdict == Verdict.PARTIALLY_CONFIRMED)
        rejected = sum(1 for c in comparisons if c.verdict == Verdict.REJECTED)
        inconclusive = sum(1 for c in comparisons if c.verdict == Verdict.INCONCLUSIVE)

        accuracy = (confirmed + 0.5 * partial) / total if total > 0 else 0.0

        recommended_deltas = []

        if accuracy < 0.3 and rejected > confirmed:
            recommended_deltas.append({
                "dimension": "hypothesis_quality",
                "change": (
                    f"Rejected outcomes ({rejected}/{total}) significantly outnumber "
                    f"confirmed ones ({confirmed}). Hypothesis formulation requires "
                    f"higher conviction thresholds and stricter validation."
                ),
                "confidence": min(0.8, 0.4 + (0.3 - accuracy)),
                "rationale": f"Accuracy {accuracy:.0%} with {rejected} rejections vs {confirmed} confirmations",
            })
            recommended_deltas.append({
                "dimension": "calibration",
                "change": (
                    f"Prediction calibration is off: only {accuracy:.0%} accuracy. "
                    f"Confidence estimates need recalibration downward by {int((0.5 - accuracy) * 100)}%."
                ),
                "confidence": min(0.7, 0.3 + (0.3 - accuracy)),
                "rationale": f"Accuracy {accuracy:.0%} below 0.3 threshold",
            })

        if accuracy > 0.7 and confirmed > rejected * 3:
            recommended_deltas.append({
                "dimension": "knowledge_yield",
                "change": (
                    f"High confirmation rate ({confirmed}/{total} confirmed, "
                    f"{accuracy:.0%} accuracy). Knowledge extraction opportunities "
                    f"are being underutilized."
                ),
                "confidence": min(0.7, 0.3 + accuracy * 0.3),
                "rationale": f"Accuracy {accuracy:.0%} with {confirmed} confirmations",
            })
            recommended_deltas.append({
                "dimension": "calibration",
                "change": (
                    f"Prediction calibration is strong ({accuracy:.0%} accuracy). "
                    f"Confidence estimates can be maintained or slightly increased."
                ),
                "confidence": min(0.6, 0.3 + accuracy * 0.3),
                "rationale": f"Accuracy {accuracy:.0%} above 0.7 threshold",
            })

        if inconclusive > total * 0.3:
            recommended_deltas.append({
                "dimension": "decision_quality",
                "change": (
                    f"{inconclusive}/{total} ({inconclusive/total:.0%}) outcomes are "
                    f"inconclusive. Decision criteria need refinement to produce "
                    f"more definitive predictions."
                ),
                "confidence": min(0.6, 0.3 + inconclusive / total * 0.3),
                "rationale": f"{inconclusive}/{total} inconclusive outcomes",
            })

        if rejected > confirmed * 2 and rejected > 5:
            recommended_deltas.append({
                "dimension": "hypothesis_quality",
                "change": (
                    f"High rejection rate ({rejected}/{total}). Hypothesis "
                    f"formulation is producing too many false positives."
                ),
                "confidence": min(0.8, 0.5 + rejected / max(total, 1) * 0.3),
                "rationale": f"{rejected} rejections vs {confirmed} confirmations",
            })

        return {
            "total_analyzed": total,
            "confirmed": confirmed,
            "partial": partial,
            "rejected": rejected,
            "inconclusive": inconclusive,
            "accuracy": round(accuracy, 3),
            "recommended_deltas": recommended_deltas,
            "patterns": {
                "high_accuracy_confirm": accuracy > 0.7,
                "low_accuracy_reject": accuracy < 0.3,
                "high_inconclusive": inconclusive > total * 0.3,
                "rejection_dominated": rejected > confirmed * 2 and rejected > 5,
            },
        }

    def generate_candidates(
        self,
        analysis: Dict[str, Any],
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        if analysis["total_analyzed"] == 0:
            return {
                "candidates_generated": 0,
                "dry_run": dry_run,
                "candidates": [],
            }

        existing = self.store.list_criterion_deltas(limit=10000)
        existing_dimensions = set(d.dimension for d in existing
                                  if d.status == DeltaStatus.PENDING_REVIEW)

        generated = []
        for rec in analysis.get("recommended_deltas", []):
            dimension = rec["dimension"]
            if dimension in existing_dimensions:
                continue
            if dimension not in VALID_DIMENSIONS:
                continue

            candidate = CriterionDelta(
                id=str(uuid.uuid4()),
                proposed_by="CriterionCandidateGenerator",
                source_evidence={
                    "hypotheses": [],
                    "knowledge": [],
                    "outcomes": analysis.get("total_analyzed", 0),
                },
                dimension=dimension,
                change=rec["change"],
                confidence=rec.get("confidence", 0.5),
                status=DeltaStatus.PENDING_REVIEW,
                created_at=datetime.now(timezone.utc),
            )

            if not dry_run:
                self.store.create_criterion_delta(candidate)

            generated.append(candidate)

        return {
            "candidates_generated": len(generated),
            "dry_run": dry_run,
            "candidates": generated,
        }

    def run_pipeline(
        self, outcome_limit: int = 100, dry_run: bool = True
    ) -> Dict[str, Any]:
        analysis = self.analyze_recent_outcomes(limit=outcome_limit)
        result = self.generate_candidates(analysis, dry_run=dry_run)
        return {"analysis": analysis, "generation": result}

    def get_candidate_stats(self) -> Dict[str, Any]:
        deltas = self.store.list_criterion_deltas(limit=10000)
        pending = sum(1 for d in deltas if d.status == DeltaStatus.PENDING_REVIEW)
        applied = sum(1 for d in deltas if d.status == DeltaStatus.APPLIED)
        rejected = sum(1 for d in deltas if d.status == DeltaStatus.REJECTED)
        return {
            "total_deltas": len(deltas),
            "pending_review": pending,
            "applied": applied,
            "rejected": rejected,
            "dimensions_affected": len(set(d.dimension for d in deltas)),
        }
