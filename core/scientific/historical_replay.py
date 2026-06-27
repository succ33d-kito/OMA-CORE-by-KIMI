"""O.M.A.-C.O.R.E. Historical Learning Replay

Transforms historical trade records into scientific learning objects
(OutcomeComparison, Knowledge, CriterionDelta) to validate that
the Learning Core can learn from past experience.

Offline, read-only, isolated from the operational pipeline.
"""
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
)
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.scientific.outcome_comparison import compare_outcome, auto_detect_verdict
from core.scientific.knowledge_lifecycle import extract_knowledge, promote_to_provisional
from core.scientific.criterion_evolution import propose_delta
from core.scientific.scientific_store import ScientificStore


REPLAY_PROVENANCE = "generated_from_historical_replay"
REPORT_DIR = Path("_project-memory") / "learning_replay"


class LearningSession:
    """Summary of one replay run.

    Not a schema — exists only as a JSON report until the Learning
    Core roadmap advances to formalize session tracking.
    """

    def __init__(self, source: str, is_dry_run: bool):
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.source = source
        self.is_dry_run = is_dry_run
        self.records_read = 0
        self.hypotheses_created = 0
        self.comparisons_created = 0
        self.knowledge_created = 0
        self.criterion_deltas_proposed = 0
        self.verdict_distribution: Dict[str, int] = {}
        self.error_type_distribution: Dict[str, int] = {}
        self.confidence_distribution: Dict[str, int] = {
            "0.0-0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-1.0": 0,
        }
        self.missing_fields_summary: Dict[str, int] = {}
        self.warnings: List[str] = []
        self.recommended_next_action: str = "Review replay report and validate knowledge quality before proceeding to Stage 9."

    def record_verdict(self, verdict: Verdict) -> None:
        key = verdict.value
        self.verdict_distribution[key] = self.verdict_distribution.get(key, 0) + 1

    def record_error_type(self, error_type: Optional[ErrorType]) -> None:
        if error_type:
            key = error_type.value
            self.error_type_distribution[key] = self.error_type_distribution.get(key, 0) + 1

    def record_confidence(self, confidence: float) -> None:
        if confidence < 0.3:
            self.confidence_distribution["0.0-0.3"] += 1
        elif confidence < 0.5:
            self.confidence_distribution["0.3-0.5"] += 1
        elif confidence < 0.7:
            self.confidence_distribution["0.5-0.7"] += 1
        else:
            self.confidence_distribution["0.7-1.0"] += 1

    def record_missing_fields(self, fields: List[str]) -> None:
        for f in fields:
            self.missing_fields_summary[f] = self.missing_fields_summary.get(f, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "mode": "dry_run" if self.is_dry_run else "commit",
            "records_read": self.records_read,
            "hypotheses_created": self.hypotheses_created,
            "comparisons_created": self.comparisons_created,
            "knowledge_created": self.knowledge_created,
            "criterion_deltas_proposed": self.criterion_deltas_proposed,
            "verdict_distribution": self.verdict_distribution,
            "error_type_distribution": self.error_type_distribution,
            "confidence_distribution": self.confidence_distribution,
            "missing_fields_summary": self.missing_fields_summary,
            "warnings": self.warnings,
            "recommended_next_action": self.recommended_next_action,
        }

    def save_report(self, report_dir: Optional[Path] = None) -> Path:
        out_dir = report_dir or REPORT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = self.timestamp.strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"learning_replay_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    def print_summary(self) -> None:
        print(f"\n{'=' * 55}")
        print(f"  Learning Replay Session Summary")
        print(f"{'=' * 55}")
        print(f"  Session ID:  {self.session_id[:16]}...")
        print(f"  Timestamp:   {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  Source:      {self.source}")
        print(f"  Mode:        {'DRY RUN' if self.is_dry_run else 'COMMIT'}")
        print(f"  Records:     {self.records_read}")
        print(f"  Hypotheses:  {self.hypotheses_created}")
        print(f"  Comparisons: {self.comparisons_created}")
        print(f"  Knowledge:   {self.knowledge_created}")
        print(f"  Deltas:      {self.criterion_deltas_proposed}")
        print(f"\n  Verdict Distribution:")
        for v, c in sorted(self.verdict_distribution.items()):
            pct = c / self.comparisons_created * 100 if self.comparisons_created else 0
            print(f"    {v:20s}: {c:3d} ({pct:5.1f}%)")
        if self.missing_fields_summary:
            print(f"\n  Missing Fields:")
            for f, c in sorted(self.missing_fields_summary.items()):
                print(f"    {f:25s}: {c}")
        if self.warnings:
            print(f"\n  Warnings:")
            for w in self.warnings:
                print(f"    ⚠ {w}")
        print(f"\n  → {self.recommended_next_action}")
        print(f"{'=' * 55}\n")


COMMON_TRADE_FIELDS = {
    "id": ["id", "trade_id"],
    "asset": ["asset", "symbol", "instrument", "pair"],
    "direction": ["direction", "side", "action"],
    "entry_price": ["entry_price", "entry", "open_price"],
    "exit_price": ["exit_price", "exit", "close_price"],
    "entry_time": ["entry_time", "entry_at", "opened_at", "open_time"],
    "exit_time": ["exit_time", "exit_at", "closed_at", "close_time"],
    "pnl_percent": ["pnl_percent", "pnl_pct", "return_pct", "profit_loss_pct"],
    "pnl_absolute": ["pnl_absolute", "pnl", "profit_loss", "return_abs"],
    "exit_reason": ["exit_reason", "close_reason", "reason"],
    "confidence": ["confidence", "conviction", "score"],
    "hypothesis_statement": ["hypothesis_statement", "hypothesis", "signal_reason", "reason", "entry_reason", "rationale"],
}


def _find_field(record: Dict[str, Any], field_names: List[str]) -> Optional[Any]:
    """Find a field value from a list of possible names."""
    for name in field_names:
        if name in record and record[name] is not None:
            return record[name]
    return None


def _normalize_direction(direction: Any) -> Optional[str]:
    if direction is None:
        return None
    d = str(direction).lower().strip()
    if d in ("long", "buy", "bullish", "1", "true"):
        return "long"
    if d in ("short", "sell", "bearish", "-1", "false"):
        return "short"
    return None


def _determine_verdict_from_pnl(pnl_pct: Optional[float], direction: Optional[str]) -> Optional[Verdict]:
    if pnl_pct is None:
        return None
    if pnl_pct > 0:
        return Verdict.CONFIRMED
    if pnl_pct < 0:
        return Verdict.REJECTED
    return Verdict.INCONCLUSIVE


def _determine_verdict_from_exit(exit_reason: Optional[str], direction: Optional[str], pnl_pct: Optional[float]) -> Optional[Verdict]:
    if pnl_pct is not None:
        return _determine_verdict_from_pnl(pnl_pct, direction)
    if exit_reason:
        reason = exit_reason.lower().strip()
        if reason in ("take_profit", "take profit", "tp", "trailing_stop", "trailing stop"):
            return Verdict.CONFIRMED
        if reason in ("stop_loss", "stop loss", "sl", "signal_reversal", "signal reversal"):
            return Verdict.REJECTED
    return None


def _generate_hypothesis_statement(record: Dict[str, Any]) -> str:
    statement = _find_field(record, COMMON_TRADE_FIELDS["hypothesis_statement"])
    if statement:
        return str(statement)
    asset = _find_field(record, COMMON_TRADE_FIELDS["asset"]) or "unknown_asset"
    direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"])) or "unknown_direction"
    return f"Historical trade suggested {direction} position in {asset} would be profitable"


def _missing_fields(record: Dict[str, Any]) -> List[str]:
    missing = []
    for group, names in COMMON_TRADE_FIELDS.items():
        if group == "hypothesis_statement":
            continue
        if _find_field(record, names) is None:
            missing.append(group)
    return missing


class HistoricalReplay:
    """Core replay engine: transforms historical records → scientific objects."""

    def __init__(
        self,
        source: str,
        store: Optional[ScientificStore] = None,
        is_dry_run: bool = True,
        limit: int = 100,
    ):
        self.source = source
        self.store = store or ScientificStore()
        self.is_dry_run = is_dry_run
        self.limit = limit
        self.session = LearningSession(source=source, is_dry_run=is_dry_run)
        self._hypotheses: List[Hypothesis] = []
        self._comparisons: List[OutcomeComparison] = []
        self._knowledge_list: List[Knowledge] = []
        self._deltas: List[CriterionDelta] = []

    def run(self) -> LearningSession:
        records = self._read_source()
        if not records:
            self.session.warnings.append("No records found in source")
            return self.session

        if self.limit and self.limit < len(records):
            records = records[:self.limit]

        self.session.records_read = len(records)

        for i, record in enumerate(records):
            missing = _missing_fields(record)
            if missing:
                self.session.record_missing_fields(missing)

            try:
                hyp = self._create_hypothesis(record)
                comparison = self._compare_outcome(hyp, record)
                knowledge = self._extract_knowledge(comparison, record)
                delta = self._propose_delta(knowledge, comparison, record)

                self._hypotheses.append(hyp)
                self._comparisons.append(comparison)
                self._knowledge_list.append(knowledge)
                self._deltas.append(delta)

                if not self.is_dry_run:
                    self._persist(hyp, comparison, knowledge, delta)

                self.session.record_verdict(comparison.verdict)
                self.session.record_error_type(comparison.error_type)
                self.session.record_confidence(comparison.comparison_confidence)
                self.session.hypotheses_created += 1
                self.session.comparisons_created += 1
                self.session.knowledge_created += 1
                self.session.criterion_deltas_proposed += 1

            except Exception as e:
                self.session.warnings.append(
                    f"Failed to process record {i} ({record.get('id', record.get('trade_id', 'unknown'))}): {e}"
                )

        return self.session

    def _read_source(self) -> List[Dict[str, Any]]:
        path = Path(self.source)
        if not path.exists():
            self.session.warnings.append(f"Source not found: {self.source}")
            return []

        try:
            if path.suffix == ".json":
                return self._read_json(path)
            elif path.suffix == ".jsonl":
                return self._read_jsonl(path)
            elif path.suffix == ".db" or path.suffix == ".sqlite":
                return self._read_sqlite(path)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content.startswith("[") or content.startswith("{"):
                        return self._read_json(path)
                    return self._read_jsonl(path)
        except Exception as e:
            self.session.warnings.append(f"Failed to read source {self.source}: {e}")
            return []

    def _read_json(self, path: Path) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            records = data.get("trades", data.get("records", data.get("data", None)))
            if isinstance(records, list):
                return records
            return [data]
        return []

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def _read_sqlite(self, path: Path) -> List[Dict[str, Any]]:
        records = []
        try:
            conn = sqlite3.connect(str(path))
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            self.session.warnings.append(f"Found tables: {tables}")

            trade_tables = [t for t in tables if any(kw in t.lower() for kw in ["trade", "signal", "order", "position"])]
            if not trade_tables:
                self.session.warnings.append(
                    f"No trade-related tables found. Available: {tables}"
                )
                conn.close()
                return []

            for table in trade_tables[:2]:
                try:
                    cursor = conn.execute(f"SELECT * FROM \"{table}\" LIMIT ?", (self.limit,))
                    columns = [desc[0] for desc in cursor.description]
                    for row in cursor.fetchall():
                        records.append(dict(zip(columns, row)))
                except Exception as e:
                    self.session.warnings.append(f"Failed to read table {table}: {e}")

            conn.close()
        except Exception as e:
            self.session.warnings.append(f"SQLite error: {e}")
        return records

    def _create_hypothesis(self, record: Dict[str, Any]) -> Hypothesis:
        statement = _generate_hypothesis_statement(record)
        asset = _find_field(record, COMMON_TRADE_FIELDS["asset"]) or "unknown_asset"
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"])) or "unknown"
        confidence = _find_field(record, COMMON_TRADE_FIELDS["confidence"])
        confidence = max(0.3, min(0.7, float(confidence))) if confidence is not None else 0.5

        now = datetime.now(timezone.utc)
        return Hypothesis(
            id=str(uuid.uuid4()),
            title=f"Historical: {direction} {asset}",
            description=(
                f"Hypothesis generated from historical replay. "
                f"Original record: {record.get('id', record.get('trade_id', 'unknown'))}. "
                f"Provenance: {REPLAY_PROVENANCE}"
            ),
            predicted_consequence=statement,
            conditions="Historical replay — actual market conditions unknown",
            invalidation_conditions="Outcome contradicts predicted direction",
            confidence=confidence,
            status=HypothesisStatus.FORMULATED,
            created_at=now,
            updated_at=now,
            status_history=[{
                "from_status": "none",
                "to_status": "formulated",
                "timestamp": now.isoformat(),
                "reason": f"Generated by historical learning replay. {REPLAY_PROVENANCE}",
            }],
        )

    def _compare_outcome(self, hypothesis: Hypothesis, record: Dict[str, Any]) -> OutcomeComparison:
        pnl_pct = _find_field(record, COMMON_TRADE_FIELDS["pnl_percent"])
        exit_reason = _find_field(record, COMMON_TRADE_FIELDS["exit_reason"])
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"]))
        entry_price = _find_field(record, COMMON_TRADE_FIELDS["entry_price"])
        exit_price = _find_field(record, COMMON_TRADE_FIELDS["exit_price"])

        actual_outcome_parts = []
        if direction:
            actual_outcome_parts.append(f"{direction}")
        if pnl_pct is not None:
            actual_outcome_parts.append(f"{pnl_pct:+.2f}%")
        if exit_price:
            actual_outcome_parts.append(f"exit@{exit_price}")
        actual_outcome = " ".join(actual_outcome_parts) if actual_outcome_parts else "outcome recorded"

        verdict = _determine_verdict_from_exit(exit_reason, direction, pnl_pct)

        comparison_confidence = 0.5
        if verdict is not None and pnl_pct is not None:
            comparison_confidence = min(0.8, max(0.4, abs(pnl_pct) / 10.0 + 0.3))

        error_type = None
        error_detail = None
        if verdict == Verdict.REJECTED:
            if exit_reason:
                er = exit_reason.lower().strip()
                if er in ("stop_loss", "stop loss", "sl"):
                    error_type = ErrorType.WRONG_HYPOTHESIS
                    error_detail = "Trade hit stop loss"
                elif er in ("time_expiry", "time expiry", "expired"):
                    error_type = ErrorType.WRONG_TIMING
                    error_detail = "Trade expired before reaching target"
                else:
                    error_type = ErrorType.WRONG_HYPOTHESIS
                    error_detail = f"Exit reason: {exit_reason}"
            else:
                error_type = ErrorType.WRONG_HYPOTHESIS
                error_detail = "Negative PnL"

        if verdict is None:
            verdict = Verdict.UNKNOWN
            comparison_confidence = 0.3

        return OutcomeComparison(
            id=str(uuid.uuid4()),
            hypothesis_id=hypothesis.id,
            verdict=verdict,
            comparison_type=ComparisonType.EXECUTED,
            predicted_consequence=hypothesis.predicted_consequence,
            actual_outcome=actual_outcome,
            comparison_confidence=comparison_confidence,
            compared_at=datetime.now(timezone.utc),
            error_type=error_type,
            error_detail=error_detail,
            tolerance_applied={"replay": True, "method": "pnl_based"},
            knowledge_triggered=True,
        )

    def _extract_knowledge(self, comparison: OutcomeComparison, record: Dict[str, Any]) -> Knowledge:
        asset = _find_field(record, COMMON_TRADE_FIELDS["asset"]) or "unknown_asset"
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"])) or "unknown"
        verdict = comparison.verdict.value

        statement = (
            f"Historical replay suggests {asset} {direction} hypotheses "
            f"produced {verdict} outcomes under available trade data. "
            f"Provenance: {REPLAY_PROVENANCE}."
        )

        knowledge = extract_knowledge(
            statement=statement,
            hypothesis_ids=[comparison.hypothesis_id],
            outcome_ids=[comparison.id],
            evidence_summary=f"Verdict: {verdict}. PnL and exit data from historical trade.",
            conditions="Historical replay — market conditions inferred from trade data",
            scope="general",
            time_horizon="unknown",
            confidence=0.3,
        )

        knowledge.provenance = {
            "source": REPLAY_PROVENANCE,
            "replay_session_id": self.session.session_id,
            "source_record_id": str(record.get("id", record.get("trade_id", "unknown"))),
            "hypothesis_ids": [comparison.hypothesis_id],
            "outcome_ids": [comparison.id],
        }

        promote_to_provisional(knowledge, reason="Extracted during historical learning replay")
        return knowledge

    def _propose_delta(
        self, knowledge: Knowledge, comparison: OutcomeComparison, record: Dict[str, Any]
    ) -> CriterionDelta:
        delta = propose_delta(
            knowledge_ids=[knowledge.id],
            hypothesis_ids=[comparison.hypothesis_id],
            outcome_ids=[comparison.id],
            dimension="knowledge_yield",
            change=(
                f"Historical replay generated knowledge from {comparison.verdict.value} outcome. "
                f"Review knowledge quality before adjusting evaluation criteria."
            ),
            confidence=0.3,
            proposed_by="Historical Learning Replay",
        )
        return delta

    def _persist(
        self,
        hypothesis: Hypothesis,
        comparison: OutcomeComparison,
        knowledge: Knowledge,
        delta: CriterionDelta,
    ) -> None:
        stored_hyp = self.store.create_hypothesis(
            title=hypothesis.title,
            description=hypothesis.description,
            predicted_consequence=hypothesis.predicted_consequence,
            conditions=hypothesis.conditions,
            invalidation_conditions=hypothesis.invalidation_conditions,
            confidence=hypothesis.confidence,
        )
        comparison.hypothesis_id = stored_hyp.id
        knowledge.hypothesis_ids = [stored_hyp.id]
        delta.source_evidence["hypothesis_ids"] = [stored_hyp.id]
        self.store.create_outcome_comparison(comparison)
        self.store.create_knowledge(knowledge)
        self.store.create_criterion_delta(delta)
