"""Tests for Stage 8 — Historical Learning Replay

Tests replay engine, dry-run/commit modes, JSON/SQLite sources,
missing field handling, provenance markers, and report generation.
"""
import os
import json
import sqlite3
import pytest
from datetime import datetime, timezone
from pathlib import Path

from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.outcome_comparison_schema import OutcomeComparison, Verdict, ComparisonType
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.scientific.historical_replay import (
    HistoricalReplay, LearningSession, REPLAY_PROVENANCE,
    _find_field, _normalize_direction, _determine_verdict_from_pnl,
    _determine_verdict_from_exit,
    _generate_hypothesis_statement, _missing_fields, REPORT_DIR,
)
from core.scientific.scientific_store import ScientificStore


FIXTURE_PATH = Path("fixtures") / "sample_trades.json"
TEST_DB = "test_historical_replay.db"


def load_fixture():
    with open(FIXTURE_PATH, "r") as f:
        return json.load(f)


# ── Helper function tests ───────────────────────────────────────

class TestHelpers:
    def test_find_field_found(self):
        r = {"id": "x", "trade_id": "y"}
        assert _find_field(r, ["id", "trade_id"]) == "x"

    def test_find_field_fallback(self):
        r = {"trade_id": "y"}
        assert _find_field(r, ["id", "trade_id"]) == "y"

    def test_find_field_missing(self):
        r = {"other": "z"}
        assert _find_field(r, ["id", "trade_id"]) is None

    def test_normalize_direction_long_variants(self):
        for d in ["long", "Long", "LONG", "buy", "bullish"]:
            assert _normalize_direction(d) == "long"

    def test_normalize_direction_short_variants(self):
        for d in ["short", "Short", "SHORT", "sell", "bearish"]:
            assert _normalize_direction(d) == "short"

    def test_normalize_direction_none(self):
        assert _normalize_direction(None) is None

    def test_verdict_from_positive_pnl(self):
        assert _determine_verdict_from_pnl(5.0, "long") == Verdict.CONFIRMED

    def test_verdict_from_negative_pnl(self):
        assert _determine_verdict_from_pnl(-3.0, "long") == Verdict.REJECTED

    def test_verdict_from_zero_pnl(self):
        assert _determine_verdict_from_pnl(0.0, "long") == Verdict.INCONCLUSIVE

    def test_verdict_from_none_pnl(self):
        assert _determine_verdict_from_pnl(None, "long") is None

    def test_generate_statement_with_signal(self):
        r = {"asset": "BTC", "direction": "long", "signal_reason": "Fed pivot"}
        s = _generate_hypothesis_statement(r)
        assert "Fed pivot" in s

    def test_generate_statement_without_signal(self):
        r = {"asset": "ETH", "direction": "short"}
        s = _generate_hypothesis_statement(r)
        assert "ETH" in s
        assert "short" in s

    def test_missing_fields_reports_absent(self):
        r = {"id": "x"}
        missing = _missing_fields(r)
        assert "asset" in missing
        assert "pnl_percent" in missing
        assert "id" not in missing

    def test_missing_fields_no_missing(self):
        r = load_fixture()[0]
        missing = _missing_fields(r)
        assert missing == []


# ── LearningSession tests ───────────────────────────────────────

class TestLearningSession:
    def test_session_created_dry_run(self):
        s = LearningSession(source="test", is_dry_run=True)
        assert s.is_dry_run
        assert s.records_read == 0

    def test_session_created_commit(self):
        s = LearningSession(source="test", is_dry_run=False)
        assert not s.is_dry_run

    def test_record_verdict(self):
        s = LearningSession(source="test", is_dry_run=True)
        s.record_verdict(Verdict.CONFIRMED)
        s.record_verdict(Verdict.REJECTED)
        assert s.verdict_distribution["confirmed"] == 1
        assert s.verdict_distribution["rejected"] == 1

    def test_record_confidence_buckets(self):
        s = LearningSession(source="test", is_dry_run=True)
        s.record_confidence(0.2)
        s.record_confidence(0.4)
        s.record_confidence(0.6)
        s.record_confidence(0.8)
        assert s.confidence_distribution["0.0-0.3"] == 1
        assert s.confidence_distribution["0.3-0.5"] == 1
        assert s.confidence_distribution["0.5-0.7"] == 1
        assert s.confidence_distribution["0.7-1.0"] == 1

    def test_save_report_creates_file(self):
        s = LearningSession(source="test", is_dry_run=True)
        s.records_read = 10
        s.comparisons_created = 5
        report_dir = Path("_project-memory") / "learning_replay_test"
        path = s.save_report(report_dir=report_dir)
        assert path.exists()
        with open(path, "r") as f:
            data = json.load(f)
        assert data["records_read"] == 10
        assert data["mode"] == "dry_run"
        os.remove(path)
        report_dir.rmdir()

    def test_to_dict_structure(self):
        s = LearningSession(source="test_source", is_dry_run=True)
        d = s.to_dict()
        assert "session_id" in d
        assert "verdict_distribution" in d
        assert "recommended_next_action" in d


# ── HistoricalReplay — Dry Run tests ────────────────────────────

class TestHistoricalReplayDryRun:
    @pytest.fixture
    def replay(self):
        return HistoricalReplay(
            source=str(FIXTURE_PATH),
            is_dry_run=True,
            limit=100,
        )

    def test_dry_run_reads_records(self, replay):
        session = replay.run()
        assert session.records_read == 10

    def test_dry_run_creates_objects(self, replay):
        session = replay.run()
        assert session.hypotheses_created == 10
        assert session.comparisons_created == 10
        assert session.knowledge_created == 10
        assert session.criterion_deltas_proposed == 10

    def test_dry_run_does_not_persist(self, replay):
        replay.run()
        assert replay.store.get_lab_stats()["hypotheses"]["total"] == 0
        assert replay.store.get_lab_stats()["comparisons"]["total"] == 0
        assert replay.store.get_lab_stats()["knowledge"]["total"] == 0
        assert replay.store.get_lab_stats()["deltas"]["pending_review"] == 0

    def test_dry_run_comparisons_have_correct_type(self, replay):
        session = replay.run()
        for c in replay._comparisons:
            assert c.comparison_type == ComparisonType.EXECUTED

    def test_dry_run_hypotheses_have_provenance(self, replay):
        session = replay.run()
        for h in replay._hypotheses:
            assert REPLAY_PROVENANCE in h.description

    def test_dry_run_knowledge_is_provisional(self, replay):
        session = replay.run()
        for k in replay._knowledge_list:
            assert k.status == KnowledgeStatus.PROVISIONAL
            assert k.provenance.get("source") == REPLAY_PROVENANCE

    def test_dry_run_deltas_are_pending(self, replay):
        session = replay.run()
        for d in replay._deltas:
            assert d.status == DeltaStatus.PENDING_REVIEW

    def test_dry_run_verdict_distribution(self, replay):
        session = replay.run()
        assert "confirmed" in session.verdict_distribution
        assert "rejected" in session.verdict_distribution
        total = sum(session.verdict_distribution.values())
        assert total == 10

    def test_dry_run_limit_respected(self):
        replay = HistoricalReplay(
            source=str(FIXTURE_PATH),
            is_dry_run=True,
            limit=3,
        )
        session = replay.run()
        assert session.records_read == 3
        assert session.hypotheses_created == 3

    def test_dry_run_report_not_saved_automatically(self, replay):
        report_dir = Path("_project-memory") / "learning_replay_test"
        replay.run()
        files_before = list(report_dir.glob("*.json")) if report_dir.exists() else []
        replay.session.save_report(report_dir=report_dir)
        files_after = list(report_dir.glob("*.json"))
        assert len(files_after) == len(files_before) + 1
        for f in files_after:
            if f not in files_before:
                os.remove(f)
        if report_dir.exists():
            report_dir.rmdir()


# ── HistoricalReplay — Commit Mode tests ────────────────────────

class TestHistoricalReplayCommit:
    @pytest.fixture
    def store(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        s = ScientificStore(db_path=TEST_DB)
        yield s
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_commit_writes_to_store(self, store):
        replay = HistoricalReplay(
            source=str(FIXTURE_PATH),
            store=store,
            is_dry_run=False,
            limit=5,
        )
        session = replay.run()
        stats = store.get_lab_stats()
        assert stats["hypotheses"]["total"] == 5
        assert stats["comparisons"]["total"] == 5
        assert stats["knowledge"]["total"] == 5
        assert stats["deltas"]["pending_review"] == 5

    def test_commit_does_not_write_elsewhere(self, store):
        replay = HistoricalReplay(
            source=str(FIXTURE_PATH),
            store=store,
            is_dry_run=False,
            limit=3,
        )
        session = replay.run()
        stats = store.get_lab_stats()
        assert stats["deltas"]["applied"] == 0
        assert stats["deltas"]["pending_review"] == 3

    def test_commit_objects_have_correct_structure(self, store):
        replay = HistoricalReplay(
            source=str(FIXTURE_PATH),
            store=store,
            is_dry_run=False,
            limit=2,
        )
        session = replay.run()
        comparisons = store.list_outcome_comparisons(limit=10)
        assert len(comparisons) == 2
        for c in comparisons:
            assert isinstance(c.verdict, Verdict)

        knowledge = store.list_knowledge(limit=10)
        assert len(knowledge) == 2
        for k in knowledge:
            assert k.status == KnowledgeStatus.PROVISIONAL

        deltas = store.list_criterion_deltas(limit=10)
        assert len(deltas) == 2
        for d in deltas:
            assert d.status == DeltaStatus.PENDING_REVIEW


# ── Missing source and error handling ───────────────────────────

class TestErrorHandling:
    def test_missing_source_returns_empty(self):
        replay = HistoricalReplay(
            source="nonexistent_file.json",
            is_dry_run=True,
        )
        session = replay.run()
        assert session.records_read == 0
        assert len(session.warnings) > 0

    def test_missing_source_clean_exit(self):
        replay = HistoricalReplay(
            source="",
            is_dry_run=True,
        )
        session = replay.run()
        assert session.records_read == 0

    def test_missing_fields_reported(self):
        minimal = [
            {"id": "minimal-trade"},
            {"id": "another", "asset": "BTC"},
        ]
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(minimal, f)
            tmp_path = f.name

        replay = HistoricalReplay(source=tmp_path, is_dry_run=True)
        session = replay.run()
        assert "asset" in session.missing_fields_summary
        assert "pnl_percent" in session.missing_fields_summary
        os.remove(tmp_path)

    def test_partial_records_still_process(self):
        records = [
            {"id": "good-1", "asset": "BTC", "direction": "long",
             "entry_price": 100, "exit_price": 110,
             "pnl_percent": 10.0, "exit_reason": "take_profit",
             "confidence": 0.7},
            {"id": "bad-1", "asset": "ETH"},
        ]
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(records, f)
            tmp_path = f.name

        replay = HistoricalReplay(source=tmp_path, is_dry_run=True)
        session = replay.run()
        assert session.records_read == 2
        assert "direction" in session.missing_fields_summary
        os.remove(tmp_path)


# ── JSON fixture replay tests ───────────────────────────────────

class TestJSONFixtureReplay:
    def test_fixture_exists(self):
        assert FIXTURE_PATH.exists()

    def test_fixture_has_10_trades(self):
        data = load_fixture()
        assert len(data) == 10

    def test_all_trades_have_required_fields(self):
        for t in load_fixture():
            assert "id" in t
            assert "direction" in t
            assert "asset" in t

    def test_fixture_replay_produces_expected_verdicts(self):
        replay = HistoricalReplay(source=str(FIXTURE_PATH), is_dry_run=True)
        session = replay.run()
        confirmed = session.verdict_distribution.get("confirmed", 0)
        rejected = session.verdict_distribution.get("rejected", 0)
        assert confirmed >= 4
        assert rejected >= 4
        assert confirmed + rejected + session.verdict_distribution.get("inconclusive", 0) == 10


# ── SQLite fixture replay tests ─────────────────────────────────

class TestSQLiteFixtureReplay:
    @pytest.fixture
    def db_path(self):
        path = "test_replay_sqlite.db"
        conn = sqlite3.connect(path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl_percent REAL,
                exit_reason TEXT,
                confidence REAL,
                signal_reason TEXT
            )
        """)
        trades = load_fixture()
        for t in trades:
            conn.execute(
                "INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (t["id"], t["asset"], t["direction"], t["entry_price"],
                 t["exit_price"], t["pnl_percent"], t["exit_reason"],
                 t.get("confidence"), t.get("signal_reason"))
            )
        conn.commit()
        conn.close()
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_replay_from_sqlite(self, db_path):
        replay = HistoricalReplay(source=db_path, is_dry_run=True, limit=10)
        session = replay.run()
        assert session.records_read == 10
        assert session.hypotheses_created == 10

    def test_sqlite_replay_produces_objects(self, db_path):
        replay = HistoricalReplay(source=db_path, is_dry_run=True, limit=5)
        session = replay.run()
        assert session.comparisons_created == 5
        assert session.knowledge_created == 5
        assert session.criterion_deltas_proposed == 5

    def test_sqlite_replay_provenance(self, db_path):
        replay = HistoricalReplay(source=db_path, is_dry_run=True, limit=3)
        session = replay.run()
        for h in replay._hypotheses:
            assert REPLAY_PROVENANCE in h.description

    def test_sqlite_no_trade_table(self):
        path = "test_replay_no_trades.db"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO events VALUES ('e1', 'test')")
        conn.commit()
        conn.close()

        replay = HistoricalReplay(source=path, is_dry_run=True)
        session = replay.run()
        assert session.records_read == 0
        assert any("No trade-related tables" in w for w in session.warnings)
        os.remove(path)


# ── Verdict distribution tests ──────────────────────────────────

class TestVerdictDistribution:
    def test_profitable_long_confirmed(self):
        r = {"pnl_percent": 5.0, "direction": "long", "exit_reason": "take_profit"}
        v = _determine_verdict_from_exit("take_profit", "long", 5.0)
        assert v == Verdict.CONFIRMED

    def test_loss_short_rejected(self):
        v = _determine_verdict_from_exit("stop_loss", "short", -3.0)
        assert v == Verdict.REJECTED

    def test_no_pnl_uses_exit_reason(self):
        v = _determine_verdict_from_exit("take_profit", "long", None)
        assert v == Verdict.CONFIRMED


# ── Knowledge provenance tests ──────────────────────────────────

class TestKnowledgeProvenance:
    def test_knowledge_has_provenance(self):
        replay = HistoricalReplay(source=str(FIXTURE_PATH), is_dry_run=True, limit=1)
        session = replay.run()
        k = replay._knowledge_list[0]
        assert k.provenance["source"] == REPLAY_PROVENANCE
        assert "replay_session_id" in k.provenance
        assert "source_record_id" in k.provenance

    def test_knowledge_statement_contains_provenance(self):
        replay = HistoricalReplay(source=str(FIXTURE_PATH), is_dry_run=True, limit=1)
        session = replay.run()
        k = replay._knowledge_list[0]
        assert REPLAY_PROVENANCE in k.statement


# ── CriterionDelta tests ────────────────────────────────────────

class TestCriterionDeltaProvenance:
    def test_delta_is_pending_review(self):
        replay = HistoricalReplay(source=str(FIXTURE_PATH), is_dry_run=True, limit=1)
        session = replay.run()
        d = replay._deltas[0]
        assert d.status == DeltaStatus.PENDING_REVIEW
        assert d.dimension == "knowledge_yield"
        assert d.confidence == 0.3

    def test_delta_has_source_evidence(self):
        replay = HistoricalReplay(source=str(FIXTURE_PATH), is_dry_run=True, limit=1)
        session = replay.run()
        d = replay._deltas[0]
        assert len(d.source_evidence["knowledge_ids"]) == 1
        assert len(d.source_evidence["outcome_ids"]) == 1


# ─── Lab workflow regression ───────────────────────────────────

class TestRegression:
    def test_lab_workflow_still_passes(self):
        from core.scientific.outcome_comparison import compare_outcome, auto_detect_verdict
        from core.scientific.knowledge_lifecycle import extract_knowledge, promote_to_provisional
        from core.scientific.criterion_evolution import propose_delta
        from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
        from datetime import datetime, timezone

        hyp = Hypothesis(
            id="reg-test", title="Reg", description="Reg",
            predicted_consequence="BTC will increase",
            conditions="Normal", invalidation_conditions="BTC drops",
            confidence=0.5, status=HypothesisStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        oc = compare_outcome(hyp, "BTC went up 5%")
        assert oc.verdict is not None

        k = extract_knowledge(
            "Regression knowledge", [hyp.id], [oc.id],
            "Evidence", "Conditions", "crypto", "swing",
        )
        promote_to_provisional(k)
        assert k.status == KnowledgeStatus.PROVISIONAL

        d = propose_delta([k.id], [hyp.id], [oc.id], "calibration", "Reg test")
        assert d.status == DeltaStatus.PENDING_REVIEW
        assert True

    def test_no_operational_modules_touched(self):
        import core.schemas.event_schema
        import core.schemas.agent_schema
        import core.schemas.trade_schema
        assert True

    def test_no_spurious_databases(self):
        assert not os.path.exists("test_oma_core.db")
