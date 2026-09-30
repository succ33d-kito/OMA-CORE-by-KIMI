"""Append-only paper decision journal; no execution or criterion authority."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import sqlite3


def _utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return value.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    event_id: str
    hypothesis_id: str | None
    decided_at: datetime
    available_at: datetime
    action: str
    alternative_actions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    market_state_id: str | None
    expected_outcome: str
    invalidation_condition: str
    risk_constraints: tuple[str, ...]
    missing_information: tuple[str, ...]
    rationale: str = ""
    market_state_snapshot: str | None = None
    regime_snapshot: str | None = None

    def __post_init__(self) -> None:
        if not self.decision_id or not self.event_id or not self.action:
            raise ValueError("decision_id, event_id and action are required")
        _utc(self.decided_at)
        _utc(self.available_at)
        if self.available_at > self.decided_at:
            raise ValueError("information cannot become available after the decision")
        if not self.expected_outcome or not self.invalidation_condition:
            raise ValueError("expected outcome and invalidation condition are required")

    def to_dict(self) -> dict:
        result = asdict(self)
        result["decided_at"] = _utc(self.decided_at)
        result["available_at"] = _utc(self.available_at)
        return result


@dataclass(frozen=True)
class DecisionOutcome:
    decision_id: str
    outcome_id: str
    observed_at: datetime
    facts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.decision_id or not self.outcome_id or not self.facts:
            raise ValueError("outcome needs a decision, id and factual observations")
        _utc(self.observed_at)

    def to_dict(self) -> dict:
        result = asdict(self)
        result["observed_at"] = _utc(self.observed_at)
        return result


class DecisionJournal:
    """Persists immutable decisions and later observations in separate tables."""

    def __init__(self, path: str):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("CREATE TABLE IF NOT EXISTS decision_records (id TEXT PRIMARY KEY, decided_at TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS decision_outcomes (id TEXT PRIMARY KEY, decision_id TEXT NOT NULL REFERENCES decision_records(id), observed_at TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS paper_checkpoint (id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL)")

    def record(self, decision: DecisionRecord) -> None:
        payload = json.dumps(decision.to_dict(), sort_keys=True)
        with sqlite3.connect(self.path) as db:
            existing = db.execute("SELECT payload FROM decision_records WHERE id = ?", (decision.decision_id,)).fetchone()
            if existing:
                if existing[0] != payload:
                    raise ValueError("decision_id already exists with different information")
                return
            db.execute("INSERT INTO decision_records VALUES (?, ?, ?)", (decision.decision_id, _utc(decision.decided_at), payload))

    def observe(self, outcome: DecisionOutcome) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA foreign_keys = ON")
            self._observe_in_transaction(db, outcome)

    @staticmethod
    def _observe_in_transaction(db, outcome: DecisionOutcome) -> None:
        payload = json.dumps(outcome.to_dict(), sort_keys=True)
        row = db.execute("SELECT decided_at FROM decision_records WHERE id = ?", (outcome.decision_id,)).fetchone()
        if row is None:
            raise ValueError("outcome has no recorded decision")
        if outcome.observed_at < datetime.fromisoformat(row[0]):
            raise ValueError("outcome predates decision")
        existing = db.execute("SELECT payload FROM decision_outcomes WHERE id = ?", (outcome.outcome_id,)).fetchone()
        if existing:
            if existing[0] != payload:
                raise ValueError("outcome_id already exists with different facts")
            return
        db.execute("INSERT INTO decision_outcomes VALUES (?, ?, ?, ?)",
                   (outcome.outcome_id, outcome.decision_id, _utc(outcome.observed_at), payload))

    def commit_paper_state(self, state: dict, outcomes: tuple[DecisionOutcome, ...] = ()) -> None:
        """Atomically publish a portfolio snapshot and its factual outcomes."""
        payload = json.dumps(state, sort_keys=True)
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA foreign_keys = ON")
            for outcome in outcomes:
                self._observe_in_transaction(db, outcome)
            db.execute("INSERT INTO paper_checkpoint (id, payload) VALUES (1, ?) "
                       "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload", (payload,))

    def load_paper_state(self) -> dict | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM paper_checkpoint WHERE id = 1").fetchone()
        return json.loads(row[0]) if row else None

    def reconcile_uncommitted_paper_decisions(self, active_decision_ids: set[str]) -> int:
        """Mark plans absent from committed positions/outcomes as uncommitted.

        Called only at startup, after loading the last confirmed portfolio.
        It never claims that an order was filled or that a trade lost.
        """
        count = 0
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA foreign_keys = ON")
            rows = db.execute(
                "SELECT d.id, d.payload FROM decision_records d "
                "WHERE NOT EXISTS (SELECT 1 FROM decision_outcomes o WHERE o.decision_id = d.id)"
            ).fetchall()
            for decision_id, payload in rows:
                record = json.loads(payload)
                if not record["action"].startswith("paper_") or decision_id in active_decision_ids:
                    continue
                outcome = DecisionOutcome(
                    decision_id, f"paper-uncommitted:{decision_id}",
                    max(datetime.now(timezone.utc), datetime.fromisoformat(record["decided_at"])),
                    ("paper_transition_not_committed",),
                )
                self._observe_in_transaction(db, outcome)
                count += 1
        return count

    def history(self, decision_id: str) -> tuple[dict | None, list[dict]]:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM decision_records WHERE id = ?", (decision_id,)).fetchone()
            outcomes = db.execute("SELECT payload FROM decision_outcomes WHERE decision_id = ? ORDER BY observed_at, id", (decision_id,)).fetchall()
        return (json.loads(row[0]) if row else None, [json.loads(item[0]) for item in outcomes])
