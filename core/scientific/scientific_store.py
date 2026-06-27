"""O.M.A.-C.O.R.E. Scientific Memory Store

Separate SQLite database for hypothesis and evidence records.
Completely independent of the operational oma_core.db.

This store is the first implementation of Scientific Memory
as defined in 01_MVP_REDEFINITION.md Part VI.
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from core.schemas.hypothesis_schema import (
    Hypothesis,
    HypothesisStatus,
    HYPOTHESIS_TABLE_SCHEMA,
)
from core.schemas.evidence_schema import (
    Evidence,
    EvidenceDirection,
    EvidenceStatus,
    EVIDENCE_TABLE_SCHEMA,
)
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, OUTCOME_COMPARISON_TABLE_SCHEMA,
)
from core.schemas.knowledge_schema import (
    Knowledge, KnowledgeStatus, KNOWLEDGE_TABLE_SCHEMA,
)
from core.schemas.criterion_delta_schema import (
    CriterionDelta, DeltaStatus, CRITERION_DELTA_TABLE_SCHEMA,
)


class ScientificStore:
    """Persistent storage for hypotheses and evidence.

    Uses a separate SQLite database to guarantee zero impact
    on the existing operational database (oma_core.db).
    """

    def __init__(self, db_path: str = "scientific.db"):
        self.db_path = Path(db_path)
        self._init_database()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        with self._conn() as conn:
            conn.executescript(HYPOTHESIS_TABLE_SCHEMA)
            conn.executescript(EVIDENCE_TABLE_SCHEMA)
            conn.executescript(OUTCOME_COMPARISON_TABLE_SCHEMA)
            conn.executescript(KNOWLEDGE_TABLE_SCHEMA)
            conn.executescript(CRITERION_DELTA_TABLE_SCHEMA)

    # ── Hypothesis CRUD ──────────────────────────────────────────

    def create_hypothesis(
        self,
        title: str,
        description: str,
        predicted_consequence: str,
        conditions: str,
        invalidation_conditions: str,
        confidence: float = 0.5,
    ) -> Hypothesis:
        hyp = Hypothesis(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            predicted_consequence=predicted_consequence,
            conditions=conditions,
            invalidation_conditions=invalidation_conditions,
            confidence=max(0.0, min(1.0, confidence)),
            status=HypothesisStatus.FORMULATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status_history=[],
        )
        data = hyp.to_dict()
        data["status_history"] = json.dumps(data["status_history"])

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO hypotheses
                   (id, title, description, predicted_consequence,
                    conditions, invalidation_conditions, confidence,
                    status, created_at, updated_at, status_history)
                   VALUES (:id, :title, :description, :predicted_consequence,
                    :conditions, :invalidation_conditions, :confidence,
                    :status, :created_at, :updated_at, :status_history)""",
                data,
            )
        return hyp

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_hypothesis(row)

    def list_hypotheses(
        self, status: Optional[HypothesisStatus] = None, limit: int = 50
    ) -> List[Hypothesis]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM hypotheses WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM hypotheses ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [self._row_to_hypothesis(r) for r in rows]

    def update_hypothesis(self, hypothesis: Hypothesis) -> None:
        data = hypothesis.to_dict()
        data["status_history"] = json.dumps(data["status_history"])
        with self._conn() as conn:
            conn.execute(
                """UPDATE hypotheses SET
                   title=:title, description=:description,
                   predicted_consequence=:predicted_consequence,
                   conditions=:conditions,
                   invalidation_conditions=:invalidation_conditions,
                   confidence=:confidence, status=:status,
                   updated_at=:updated_at,
                   status_history=:status_history
                   WHERE id=:id""",
                data,
            )

    def delete_hypothesis(self, hypothesis_id: str) -> bool:
        """Remove a hypothesis and all linked evidence.

        Used only for testing and cleanup. Normal lifecycle
        uses ARCHIVED status, not deletion.
        """
        with self._conn() as conn:
            conn.execute("DELETE FROM evidence WHERE hypothesis_id = ?", (hypothesis_id,))
            cur = conn.execute("DELETE FROM hypotheses WHERE id = ?", (hypothesis_id,))
            return cur.rowcount > 0

    # ── Evidence CRUD ────────────────────────────────────────────

    def add_evidence(
        self,
        hypothesis_id: str,
        direction: EvidenceDirection,
        weight: float,
        content: str,
        source_id: str = "manual",
        source_reliability: float = 1.0,
        independence_score: float = 0.5,
    ) -> Optional[Evidence]:
        """Add evidence linked to an existing hypothesis.

        Returns None if the hypothesis does not exist.
        """
        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        evidence = Evidence(
            id=str(uuid.uuid4()),
            hypothesis_id=hypothesis_id,
            direction=direction,
            weight=max(0.0, min(1.0, weight)),
            content=content,
            source_id=source_id,
            source_reliability=max(0.0, min(1.0, source_reliability)),
            collected_at=datetime.now(timezone.utc),
            independence_score=max(0.0, min(1.0, independence_score)),
            status=EvidenceStatus.COLLECTED,
        )
        data = evidence.to_dict()

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO evidence
                   (id, hypothesis_id, direction, weight, content,
                    source_id, source_reliability, collected_at,
                    independence_score, status, superseded_by)
                   VALUES (:id, :hypothesis_id, :direction, :weight, :content,
                    :source_id, :source_reliability, :collected_at,
                    :independence_score, :status, :superseded_by)""",
                data,
            )
        return evidence

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM evidence WHERE id = ?", (evidence_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_evidence(row)

    def list_evidence(
        self,
        hypothesis_id: Optional[str] = None,
        direction: Optional[EvidenceDirection] = None,
        status: Optional[EvidenceStatus] = None,
        limit: int = 100,
    ) -> List[Evidence]:
        query = "SELECT * FROM evidence WHERE 1=1"
        params = []
        if hypothesis_id:
            query += " AND hypothesis_id = ?"
            params.append(hypothesis_id)
        if direction:
            query += " AND direction = ?"
            params.append(direction.value)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY collected_at DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_evidence(r) for r in rows]

    def update_evidence(self, evidence: Evidence) -> None:
        data = evidence.to_dict()
        with self._conn() as conn:
            conn.execute(
                """UPDATE evidence SET
                   direction=:direction, weight=:weight, content=:content,
                   source_id=:source_id,
                   source_reliability=:source_reliability,
                   independence_score=:independence_score,
                   status=:status, superseded_by=:superseded_by
                   WHERE id=:id""",
                data,
            )

    # ── OutcomeComparison CRUD ───────────────────────────────────

    def create_outcome_comparison(self, comparison: OutcomeComparison) -> OutcomeComparison:
        data = comparison.to_dict()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO outcome_comparisons
                   (id, hypothesis_id, decision_id, outcome_id,
                    verdict, error_type, comparison_type,
                    predicted_consequence, actual_outcome,
                    tolerance_applied, comparison_confidence,
                    error_detail, knowledge_triggered, compared_at)
                   VALUES (:id, :hypothesis_id, :decision_id, :outcome_id,
                    :verdict, :error_type, :comparison_type,
                    :predicted_consequence, :actual_outcome,
                    :tolerance_applied, :comparison_confidence,
                    :error_detail, :knowledge_triggered, :compared_at)""",
                data,
            )
        return comparison

    def get_outcome_comparison(self, comparison_id: str) -> Optional[OutcomeComparison]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM outcome_comparisons WHERE id = ?", (comparison_id,)
            ).fetchone()
        if not row:
            return None
        return OutcomeComparison.from_dict(dict(row))

    def list_outcome_comparisons(
        self,
        hypothesis_id: Optional[str] = None,
        verdict: Optional[Verdict] = None,
        limit: int = 50,
    ) -> List[OutcomeComparison]:
        query = "SELECT * FROM outcome_comparisons WHERE 1=1"
        params = []
        if hypothesis_id:
            query += " AND hypothesis_id = ?"
            params.append(hypothesis_id)
        if verdict:
            query += " AND verdict = ?"
            params.append(verdict.value)
        query += " ORDER BY compared_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [OutcomeComparison.from_dict(dict(r)) for r in rows]

    # ── Knowledge CRUD ───────────────────────────────────────────

    def create_knowledge(self, knowledge: Knowledge) -> Knowledge:
        data = knowledge.to_dict()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO knowledge
                   (id, statement, hypothesis_ids, outcome_ids,
                    missed_opportunity_ids, evidence_summary,
                    confidence, conditions, scope, time_horizon,
                    replication_count, replication_conditions,
                    contrary_evidence_count, last_validated_at,
                    expires_at, status, provenance,
                    revision_history, created_at, updated_at)
                   VALUES (:id, :statement, :hypothesis_ids, :outcome_ids,
                    :missed_opportunity_ids, :evidence_summary,
                    :confidence, :conditions, :scope, :time_horizon,
                    :replication_count, :replication_conditions,
                    :contrary_evidence_count, :last_validated_at,
                    :expires_at, :status, :provenance,
                    :revision_history, :created_at, :updated_at)""",
                data,
            )
        return knowledge

    def get_knowledge(self, knowledge_id: str) -> Optional[Knowledge]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge WHERE id = ?", (knowledge_id,)
            ).fetchone()
        if not row:
            return None
        return Knowledge.from_dict(dict(row))

    def list_knowledge(
        self,
        status: Optional[KnowledgeStatus] = None,
        limit: int = 50,
    ) -> List[Knowledge]:
        query = "SELECT * FROM knowledge WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Knowledge.from_dict(dict(r)) for r in rows]

    def update_knowledge(self, knowledge: Knowledge) -> None:
        data = knowledge.to_dict()
        with self._conn() as conn:
            conn.execute(
                """UPDATE knowledge SET
                   statement=:statement, hypothesis_ids=:hypothesis_ids,
                   outcome_ids=:outcome_ids,
                   missed_opportunity_ids=:missed_opportunity_ids,
                   evidence_summary=:evidence_summary,
                   confidence=:confidence, conditions=:conditions,
                   scope=:scope, time_horizon=:time_horizon,
                   replication_count=:replication_count,
                   replication_conditions=:replication_conditions,
                   contrary_evidence_count=:contrary_evidence_count,
                   last_validated_at=:last_validated_at,
                   expires_at=:expires_at, status=:status,
                   provenance=:provenance,
                   revision_history=:revision_history,
                   updated_at=:updated_at
                   WHERE id=:id""",
                data,
            )

    # ── CriterionDelta CRUD ──────────────────────────────────────

    def create_criterion_delta(self, delta: CriterionDelta) -> CriterionDelta:
        data = delta.to_dict()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO criterion_deltas
                   (id, proposed_by, source_evidence, dimension,
                    change, confidence, status, created_at,
                    applied_at, outcome_tracking)
                   VALUES (:id, :proposed_by, :source_evidence, :dimension,
                    :change, :confidence, :status, :created_at,
                    :applied_at, :outcome_tracking)""",
                data,
            )
        return delta

    def get_criterion_delta(self, delta_id: str) -> Optional[CriterionDelta]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM criterion_deltas WHERE id = ?", (delta_id,)
            ).fetchone()
        if not row:
            return None
        return CriterionDelta.from_dict(dict(row))

    def list_criterion_deltas(
        self,
        status: Optional[DeltaStatus] = None,
        dimension: Optional[str] = None,
        limit: int = 50,
    ) -> List[CriterionDelta]:
        query = "SELECT * FROM criterion_deltas WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if dimension:
            query += " AND dimension = ?"
            params.append(dimension)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [CriterionDelta.from_dict(dict(r)) for r in rows]

    def update_criterion_delta(self, delta: CriterionDelta) -> None:
        data = delta.to_dict()
        with self._conn() as conn:
            conn.execute(
                """UPDATE criterion_deltas SET
                   proposed_by=:proposed_by,
                   source_evidence=:source_evidence,
                   dimension=:dimension, change=:change,
                   confidence=:confidence, status=:status,
                   applied_at=:applied_at,
                   outcome_tracking=:outcome_tracking
                   WHERE id=:id""",
                data,
            )

    # ── Lab Stats ────────────────────────────────────────────────

    def get_lab_stats(self) -> dict:
        with self._conn() as conn:
            total_h = conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0]
            evaluated_h = conn.execute(
                "SELECT COUNT(*) FROM hypotheses WHERE status='evaluated'"
            ).fetchone()[0]
            total_c = conn.execute("SELECT COUNT(*) FROM outcome_comparisons").fetchone()[0]
            confirmed = conn.execute(
                "SELECT COUNT(*) FROM outcome_comparisons WHERE verdict='confirmed'"
            ).fetchone()[0]
            rejected = conn.execute(
                "SELECT COUNT(*) FROM outcome_comparisons WHERE verdict='rejected'"
            ).fetchone()[0]
            total_k = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            validated_k = conn.execute(
                "SELECT COUNT(*) FROM knowledge WHERE status='validated'"
            ).fetchone()[0]
            pending_deltas = conn.execute(
                "SELECT COUNT(*) FROM criterion_deltas WHERE status='pending_review'"
            ).fetchone()[0]
            applied_deltas = conn.execute(
                "SELECT COUNT(*) FROM criterion_deltas WHERE status='applied'"
            ).fetchone()[0]

        return {
            "hypotheses": {"total": total_h, "evaluated": evaluated_h},
            "comparisons": {"total": total_c, "confirmed": confirmed, "rejected": rejected},
            "knowledge": {"total": total_k, "validated": validated_k},
            "deltas": {"pending_review": pending_deltas, "applied": applied_deltas},
        }

    # ── Stats ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total_hypotheses = conn.execute(
                "SELECT COUNT(*) FROM hypotheses"
            ).fetchone()[0]
            by_status = conn.execute(
                "SELECT status, COUNT(*) FROM hypotheses GROUP BY status"
            ).fetchall()
            total_evidence = conn.execute(
                "SELECT COUNT(*) FROM evidence"
            ).fetchone()[0]
            evidence_by_direction = conn.execute(
                "SELECT direction, COUNT(*) FROM evidence GROUP BY direction"
            ).fetchall()

        return {
            "total_hypotheses": total_hypotheses,
            "hypotheses_by_status": {r[0]: r[1] for r in by_status},
            "total_evidence": total_evidence,
            "evidence_by_direction": {r[0]: r[1] for r in evidence_by_direction},
        }

    # ── Helpers ──────────────────────────────────────────────────

    def _row_to_hypothesis(self, row: sqlite3.Row) -> Hypothesis:
        data = dict(row)
        data["status_history"] = json.loads(data.get("status_history", "[]"))
        return Hypothesis.from_dict(data)

    def _row_to_evidence(self, row: sqlite3.Row) -> Evidence:
        return Evidence.from_dict(dict(row))
