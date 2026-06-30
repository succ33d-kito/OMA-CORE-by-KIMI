"""
knowledge_extractor.py — Convert confirmed outcomes into Knowledge objects.

Never overwrites existing knowledge. Never deletes.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.outcome_comparison_schema import Verdict
from core.scientific.scientific_store import ScientificStore


class KnowledgeExtractor:
    """Extract Knowledge objects from confirmed outcome comparisons."""

    def __init__(self, scientific_db: str = "scientific.db"):
        self.store = ScientificStore(scientific_db)

    def extract_from_comparison(
        self,
        comparison_id: str,
        statement: Optional[str] = None,
        conditions: Optional[str] = None,
        scope: str = "general",
        time_horizon: str = "swing",
        confidence: float = 0.3,
    ) -> Dict[str, Any]:
        """Extract a Knowledge object from a single outcome comparison.

        Reads the comparison from scientific.db. If no statement is provided,
        generates one from the comparison data.
        """
        comparison = self.store.get_outcome_comparison(comparison_id)
        if not comparison:
            return {"error": f"Comparison not found: {comparison_id}"}

        if comparison.verdict not in (Verdict.CONFIRMED, Verdict.PARTIALLY_CONFIRMED):
            return {
                "error": (
                    f"Comparison {comparison_id} has verdict '{comparison.verdict.value}'. "
                    f"Only CONFIRMED or PARTIALLY_CONFIRMED outcomes can produce knowledge."
                ),
            }

        hypothesis = self.store.get_hypothesis(comparison.hypothesis_id)

        generated_statement = statement or (
            f"When {comparison.predicted_consequence[:100]}, "
            f"the actual outcome was {comparison.actual_outcome[:100]}. "
            f"This pattern suggests the original reasoning has predictive value."
        )

        hypothesis_ids = [comparison.hypothesis_id]
        outcome_ids = [comparison_id]

        evidence_summary = (
            f"Outcome comparison {comparison_id}: "
            f"predicted '{comparison.predicted_consequence[:100]}', "
            f"actual '{comparison.actual_outcome[:100]}', "
            f"verdict {comparison.verdict.value}."
        )

        knowledge_conditions = conditions or (
            f"Derived from hypothesis {comparison.hypothesis_id}. "
            f"Applies when similar opportunity conditions are met."
        )

        expiry = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()

        knowledge = Knowledge(
            id=f"kn_{comparison_id[:28]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}",
            statement=generated_statement[:500],
            hypothesis_ids=hypothesis_ids,
            outcome_ids=outcome_ids,
            missed_opportunity_ids=[],
            evidence_summary=evidence_summary[:500],
            confidence=min(confidence + (0.1 if comparison.verdict == Verdict.CONFIRMED else 0.0), 0.95),
            conditions=knowledge_conditions[:500],
            scope=scope,
            time_horizon=time_horizon,
            status=KnowledgeStatus.EXTRACTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            replication_count=0,
            replication_conditions=[],
            contrary_evidence_count=0,
            last_validated_at=None,
            expires_at=datetime.fromisoformat(expiry) if isinstance(expiry, str) else expiry,
            provenance={
                "extractor": "knowledge_extractor.py",
                "source_comparison": comparison_id,
                "source_hypothesis": comparison.hypothesis_id,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "method": "auto_extract_from_confirmed_outcome",
            },
            revision_history=[],
        )

        return {
            "knowledge": knowledge,
            "source_comparison_id": comparison_id,
            "source_verdict": comparison.verdict.value,
            "confidence": knowledge.confidence,
        }

    def extract_all_confirmed(
        self,
        scope: str = "general",
        time_horizon: str = "swing",
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Extract knowledge from all CONFIRMED comparisons that haven't been extracted yet."""
        comparisons = self.store.list_outcome_comparisons(
            verdict=Verdict.CONFIRMED, limit=1000
        )
        partials = self.store.list_outcome_comparisons(
            verdict=Verdict.PARTIALLY_CONFIRMED, limit=1000
        )
        all_confirmed = comparisons + partials

        # Get existing knowledge to avoid duplicates
        existing = self.store.list_knowledge(limit=10000)
        existing_outcome_ids = set()
        for k in existing:
            existing_outcome_ids.update(k.outcome_ids)

        results = []
        for comp in all_confirmed:
            if comp.id in existing_outcome_ids:
                results.append({
                    "comparison_id": comp.id,
                    "status": "skipped_duplicate",
                })
                continue

            result = self.extract_from_comparison(
                comparison_id=comp.id,
                scope=scope,
                time_horizon=time_horizon,
                confidence=0.3,
            )
            if "error" in result:
                results.append({
                    "comparison_id": comp.id,
                    "status": "error",
                    "error": result["error"],
                })
                continue

            if not dry_run:
                self.store.create_knowledge(result["knowledge"])

            results.append({
                "comparison_id": comp.id,
                "status": "extracted" if not dry_run else "preview",
                "knowledge_id": result["knowledge"].id,
                "confidence": result["confidence"],
            })

        return {
            "confirmed_comparisons": len(all_confirmed),
            "extracted": sum(1 for r in results if r["status"] in ("extracted", "preview")),
            "skipped_duplicates": sum(1 for r in results if r["status"] == "skipped_duplicate"),
            "dry_run": dry_run,
            "results": results,
        }

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get knowledge extraction statistics."""
        knowledge_items = self.store.list_knowledge(limit=10000)
        confirmed = self.store.list_outcome_comparisons(
            verdict=Verdict.CONFIRMED, limit=10000
        )
        partial = self.store.list_outcome_comparisons(
            verdict=Verdict.PARTIALLY_CONFIRMED, limit=10000
        )
        return {
            "total_knowledge_items": len(knowledge_items),
            "confirmed_outcomes_available": len(confirmed) + len(partial),
            "knowledge_extracted": len(knowledge_items),
            "remaining_to_extract": len(confirmed) + len(partial) - len(knowledge_items),
        }
