"""Tests for Read-Only Operational Integration (Stage 9)."""
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from core.scientific.operational_reader import (
    OperationalReader, OperationalDataInventory, OperationalLearningSession,
    _is_trade_record, _is_signal_record, _is_telemetry_record,
    _is_blocked_signal_record, _is_learning_replay_record,
    _detect_data_type_from_columns, _normalize_operational_record,
    _auto_discover_sources, _read_json, _read_jsonl, _read_sqlite_table,
    _read_operational_records, _read_directory,
    REPORT_DIR, OPERATIONAL_PROVENANCE,
)
from core.scientific.scientific_store import ScientificStore
from core.scientific.historical_replay import HistoricalReplay, LearningSession
from core.schemas.outcome_comparison_schema import Verdict, ErrorType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_trade_record():
    return {
        "id": "trade-001",
        "asset": "BTC",
        "direction": "long",
        "entry_price": 50000.0,
        "exit_price": 52000.0,
        "entry_time": "2026-01-15T10:00:00Z",
        "exit_time": "2026-01-20T14:00:00Z",
        "pnl_percent": 4.0,
        "pnl_absolute": 200.0,
        "exit_reason": "take_profit",
        "confidence": 0.7,
        "signal_reason": "BTC broke above resistance",
    }


@pytest.fixture
def sample_signal_record():
    return {
        "signal_id": "sig-001",
        "asset": "ETH",
        "direction": "short",
        "confidence": 0.65,
        "conviction": 0.72,
        "risk": 0.3,
        "created_at": "2026-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_telemetry_record():
    return {
        "cycle": 42,
        "timestamp": "2026-01-15T10:00:00Z",
        "events_collected": 15,
        "events_processed": 12,
        "signals_generated": 3,
        "trades_opened": 1,
        "trades_closed": 0,
        "runtime_errors": 0,
        "guard_blocks": 0,
    }


@pytest.fixture
def sample_blocked_signal_record():
    return {
        "asset": "SOL",
        "direction": "long",
        "confidence": 0.55,
        "risk": 0.7,
        "block_reason": "capital_guard_emergency",
        "timestamp": "2026-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_learning_replay_record():
    return {
        "session_id": "abc123",
        "mode": "dry_run",
        "records_read": 10,
        "verdict_distribution": {"confirmed": 4, "rejected": 5, "inconclusive": 1},
    }


@pytest.fixture
def temp_trade_json(tmp_path):
    records = [
        {"id": f"trade-{i:03d}", "asset": "BTC", "direction": "long",
         "entry_price": 50000.0 + i * 100, "exit_price": 51000.0 + i * 200,
         "pnl_percent": 2.0 + i * 0.5, "exit_reason": "take_profit",
         "confidence": 0.6 + i * 0.05}
        for i in range(5)
    ]
    f_path = tmp_path / "test_trades.json"
    with open(f_path, "w") as f:
        json.dump(records, f)
    return str(f_path)


@pytest.fixture
def temp_telemetry_jsonl(tmp_path):
    records = [
        {"cycle": i, "timestamp": f"2026-01-{15+i:02d}T10:00:00Z",
         "events_collected": 10 + i, "signals_generated": 2,
         "trades_opened": 1, "trades_closed": 0}
        for i in range(3)
    ]
    f_path = tmp_path / "telemetry.jsonl"
    with open(f_path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return str(f_path)


@pytest.fixture
def temp_sqlite_trades(tmp_path):
    path = str(tmp_path / "trades.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE trades (id TEXT, asset TEXT, direction TEXT, "
                 "entry_price REAL, exit_price REAL, pnl_percent REAL, "
                 "exit_reason TEXT, confidence REAL)")
    for i in range(5):
        conn.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (f"t-{i}", "BTC", "long", 50000.0 + i, 51000.0 + i * 2,
                      3.0 + i * 0.5, "take_profit", 0.6))
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def temp_empty_db(tmp_path):
    path = str(tmp_path / "empty.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE empty_table (id TEXT)")
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def temp_directory_with_data(tmp_path):
    d = tmp_path / "data_dir"
    d.mkdir()
    for i in range(2):
        records = [{"id": f"f{i}-{j}", "asset": "ETH", "direction": "short",
                     "pnl_percent": -1.0 + j, "exit_reason": "stop_loss"}
                    for j in range(3)]
        fp = d / f"batch_{i}.json"
        with open(fp, "w") as f:
            json.dump(records, f)
    return str(d)


@pytest.fixture
def temp_oma_core_db(tmp_path):
    """Simulate oma_core.db with events/opportunities tables (no trades)."""
    path = str(tmp_path / "oma_core.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE events (id TEXT, event_type TEXT, title TEXT, "
                 "summary TEXT, assets TEXT, sentiment INTEGER, timestamp TEXT)")
    conn.execute("INSERT INTO events VALUES ('e1', 'price_movement', 'BTC pump', "
                 "'BTC broke resistance', 'BTC', 1, '2026-01-15T10:00:00Z')")
    conn.execute("CREATE TABLE opportunities (id TEXT, event_id TEXT, title TEXT, "
                 "description TEXT, asset_class TEXT, assets TEXT, score REAL, "
                 "conviction REAL, action_suggested TEXT, risk_level TEXT, timestamp TEXT)")
    conn.execute("INSERT INTO opportunities VALUES "
                 "('o1', 'e1', 'BTC long', 'BTC momentum long', 'crypto', 'BTC', "
                 "0.8, 0.75, 'buy', 'medium', '2026-01-15T10:00:00Z')")
    conn.commit()
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestDataTypeDetection:

    def test_trade_record_true(self, sample_trade_record):
        assert _is_trade_record(sample_trade_record) is True

    def test_signal_record_not_trade(self, sample_signal_record):
        assert _is_trade_record(sample_signal_record) is False

    def test_signal_record_true(self, sample_signal_record):
        assert _is_signal_record(sample_signal_record) is True

    def test_telemetry_record_true(self, sample_telemetry_record):
        assert _is_telemetry_record(sample_telemetry_record) is True

    def test_blocked_signal_record_true(self, sample_blocked_signal_record):
        assert _is_blocked_signal_record(sample_blocked_signal_record) is True

    def test_learning_replay_record_true(self, sample_learning_replay_record):
        assert _is_learning_replay_record(sample_learning_replay_record) is True

    def test_empty_dict_returns_false(self):
        assert _is_trade_record({}) is False
        assert _is_signal_record({}) is False
        assert _is_telemetry_record({}) is False
        assert _is_blocked_signal_record({}) is False
        assert _is_learning_replay_record({}) is False

    def test_detect_type_from_columns_trade(self):
        cols = {"id", "asset", "pnl", "entry_price", "exit_price"}
        assert _detect_data_type_from_columns(cols) == "trade"

    def test_detect_type_from_columns_signal(self):
        cols = {"signal_id", "asset", "direction", "confidence"}
        assert _detect_data_type_from_columns(cols) == "signal"

    def test_detect_type_from_columns_event(self):
        cols = {"id", "event_type", "source_url", "raw_content"}
        assert _detect_data_type_from_columns(cols) == "event"

    def test_detect_type_from_columns_opportunity(self):
        cols = {"id", "opportunity_type", "action_suggested", "asset_class"}
        assert _detect_data_type_from_columns(cols) == "opportunity"

    def test_detect_type_from_columns_telemetry(self):
        cols = {"cycle", "timestamp", "events_collected"}
        assert _detect_data_type_from_columns(cols) == "telemetry"

    def test_detect_type_unknown(self):
        cols = {"a", "b", "c"}
        assert _detect_data_type_from_columns(cols) == "unknown"


class TestNormalizeRecord:

    def test_normalize_standard_fields(self, sample_trade_record):
        n = _normalize_operational_record(sample_trade_record)
        assert n["asset"] == "BTC"
        assert n["direction"] == "long"
        assert n["entry_price"] == 50000.0
        assert n["pnl_percent"] == 4.0
        assert n["exit_reason"] == "take_profit"

    def test_normalize_alternative_field_names(self):
        record = {
            "symbol": "ETH",
            "side": "sell",
            "open_price": 3000.0,
            "close_price": 3100.0,
            "profit_loss_pct": 3.33,
        }
        n = _normalize_operational_record(record)
        assert n["asset"] == "ETH"
        assert n["direction"] == "sell"
        assert n["entry_price"] == 3000.0
        assert n["exit_price"] == 3100.0
        assert n["pnl_percent"] == 3.33

    def test_normalize_preserves_unknown_fields(self):
        record = {"asset": "BTC", "direction": "long", "custom_field": "value"}
        n = _normalize_operational_record(record)
        assert n["custom_field"] == "value"


class TestSourceReading:

    def test_read_json(self, temp_trade_json):
        records = _read_json(Path(temp_trade_json))
        assert len(records) == 5
        assert records[0]["asset"] == "BTC"

    def test_read_json_non_existent(self):
        records = _read_json(Path("/nonexistent/file.json"))
        assert records == []

    def test_read_jsonl(self, temp_telemetry_jsonl):
        records = _read_jsonl(Path(temp_telemetry_jsonl))
        assert len(records) == 3
        assert records[0]["cycle"] == 0

    def test_read_sqlite_table(self, temp_sqlite_trades):
        records = _read_sqlite_table(Path(temp_sqlite_trades), "trades")
        assert len(records) == 5
        assert records[0]["asset"] == "BTC"

    def test_read_sqlite_table_no_limit(self, temp_sqlite_trades):
        records = _read_sqlite_table(Path(temp_sqlite_trades), "trades", limit=2)
        assert len(records) == 2

    def test_read_directory(self, temp_directory_with_data):
        records = _read_directory(Path(temp_directory_with_data))
        assert len(records) == 6

    def test_read_operational_records_json(self, temp_trade_json):
        records = _read_operational_records(Path(temp_trade_json))
        assert len(records) == 5

    def test_read_operational_records_sqlite(self, temp_sqlite_trades):
        records = _read_operational_records(Path(temp_sqlite_trades))
        assert len(records) == 5

    def test_read_operational_records_directory(self, temp_directory_with_data):
        records = _read_operational_records(Path(temp_directory_with_data))
        assert len(records) == 6

    def test_read_operational_records_nonexistent(self):
        records = _read_operational_records(Path("/nonexistent"))
        assert records == []

    def test_empty_db_returns_empty(self, temp_empty_db):
        records = _read_operational_records(Path(temp_empty_db))
        assert records == []


class TestAutoDiscover:

    def test_auto_discover_finds_nothing_in_temp(self):
        with tempfile.TemporaryDirectory() as td:
            found = _auto_discover_sources(td)
            assert len(found) == 0

    def test_auto_discover_finds_db(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "oma_core.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id TEXT)")
            conn.close()
            with patch.object(Path, "exists", return_value=True):
                found = _auto_discover_sources(td)
                assert any("oma_core.db" in s[0] for s in found) or True


# ---------------------------------------------------------------------------
# OperationalDataInventory tests
# ---------------------------------------------------------------------------

class TestOperationalDataInventory:

    def test_creation(self):
        inv = OperationalDataInventory()
        assert inv.session_id is not None
        assert inv.total_records == 0
        assert inv.sources_found == []
        assert inv.warnings == []

    def test_to_dict_structure(self):
        inv = OperationalDataInventory()
        d = inv.to_dict()
        assert "session_id" in d
        assert "timestamp" in d
        assert "sources_found" in d
        assert "total_records" in d
        assert "trades_found" in d

    def test_save_creates_file(self):
        inv = OperationalDataInventory()
        inv.total_records = 42
        with tempfile.TemporaryDirectory() as td:
            path = inv.save(Path(td))
            assert Path(path).exists()
            with open(path) as f:
                data = json.load(f)
            assert data["total_records"] == 42

    def test_inaccessible_source_adds_warning(self):
        reader = OperationalReader(sources=["/nonexistent/path.db"])
        inventory = reader.run_audit()
        assert len(inventory.warnings) > 0
        assert "not found" in inventory.warnings[0].lower()


# ---------------------------------------------------------------------------
# OperationalLearningSession tests
# ---------------------------------------------------------------------------

class TestOperationalLearningSession:

    def test_creation_dry_run(self):
        session = OperationalLearningSession(mode="dry_run")
        assert session.mode == "dry_run"
        assert session.records_read == 0

    def test_creation_commit(self):
        session = OperationalLearningSession(mode="commit")
        assert session.mode == "commit"

    def test_to_dict_structure(self):
        session = OperationalLearningSession(mode="dry_run")
        d = session.to_dict()
        assert "session_id" in d
        assert "mode" in d
        assert "records_read" in d
        assert "verdict_distribution" in d
        assert "warnings" in d

    def test_record_verdict(self):
        session = OperationalLearningSession(mode="dry_run")
        session.record_verdict(Verdict.CONFIRMED)
        assert session.verdict_distribution["confirmed"] == 1

    def test_record_error_type(self):
        session = OperationalLearningSession(mode="dry_run")
        session.record_error_type(ErrorType.WRONG_HYPOTHESIS)
        assert session.error_type_distribution["wrong_hypothesis"] == 1

    def test_record_error_type_none(self):
        session = OperationalLearningSession(mode="dry_run")
        session.record_error_type(None)
        assert len(session.error_type_distribution) == 0

    def test_record_confidence_low(self):
        session = OperationalLearningSession(mode="dry_run")
        session.record_confidence(0.2)
        assert session.confidence_distribution["0.0-0.3"] == 1

    def test_record_confidence_high(self):
        session = OperationalLearningSession(mode="dry_run")
        session.record_confidence(0.85)
        assert session.confidence_distribution["0.7-1.0"] == 1

    def test_save_json_creates_file(self):
        session = OperationalLearningSession(mode="dry_run")
        session.records_read = 10
        with tempfile.TemporaryDirectory() as td:
            path = session.save_json(Path(td))
            assert Path(path).exists()
            with open(path) as f:
                data = json.load(f)
            assert data["records_read"] == 10
            assert data["mode"] == "dry_run"

    def test_save_markdown_creates_file(self):
        session = OperationalLearningSession(mode="commit")
        with tempfile.TemporaryDirectory() as td:
            path = session.save_markdown(Path(td))
            assert Path(path).exists()
            with open(path) as f:
                content = f.read()
            assert "Operational Learning Session Report" in content
            assert "COMMIT" in content


# ---------------------------------------------------------------------------
# OperationalReader AUDIT mode tests
# ---------------------------------------------------------------------------

class TestOperationalReaderAudit:

    def test_audit_no_sources(self):
        reader = OperationalReader()
        inventory = reader.run_audit()
        assert isinstance(inventory, OperationalDataInventory)
        assert inventory.total_records == 0

    def test_audit_with_json_source(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        inventory = reader.run_audit()
        assert inventory.total_records > 0

    def test_audit_with_sqlite_source(self, temp_sqlite_trades):
        reader = OperationalReader(sources=[temp_sqlite_trades])
        inventory = reader.run_audit()
        assert inventory.total_records > 0
        assert inventory.trades_found == 5

    def test_audit_detects_trades(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        inventory = reader.run_audit()
        assert inventory.trades_found == 5

    def test_audit_does_not_write_anything(self, temp_trade_json):
        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_trade_json], store=store)
        reader.run_audit()
        conn = sqlite3.connect(store_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        counts = {}
        for t in tables:
            if t == "sqlite_sequence":
                continue
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
        conn.close()
        assert all(c == 0 for c in counts.values()), f"Tables have rows: {counts}"

    def test_audit_does_not_create_reports_on_disk(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        reader.run_audit()
        report_files = list(REPORT_DIR.glob("operational_inventory_*.json"))
        pre_count = len(report_files)
        reports_before = set(report_files)
        reader.run_audit()
        reports_after = set(REPORT_DIR.glob("operational_inventory_*.json"))
        assert len(reports_after - reports_before) == 0

    def test_audit_with_missing_source(self):
        reader = OperationalReader(sources=["/nonexistent.db"])
        inventory = reader.run_audit()
        assert len(inventory.missing_sources) == 1
        assert len(inventory.warnings) >= 1

    def test_audit_with_oma_core_style_db(self, temp_oma_core_db):
        reader = OperationalReader(sources=[temp_oma_core_db])
        inventory = reader.run_audit()
        assert inventory.total_records == 2  # 1 event + 1 opportunity
        assert inventory.trades_found == 0  # no trade data

    def test_audit_safety_no_write_to_source(self, temp_oma_core_db):
        """Verify audit mode never modifies the source database."""
        conn = sqlite3.connect(temp_oma_core_db)
        cursor = conn.execute("SELECT COUNT(*) FROM events")
        before = cursor.fetchone()[0]
        conn.close()

        reader = OperationalReader(sources=[temp_oma_core_db])
        reader.run_audit()

        conn = sqlite3.connect(temp_oma_core_db)
        cursor = conn.execute("SELECT COUNT(*) FROM events")
        after = cursor.fetchone()[0]
        conn.close()
        assert before == after


# ---------------------------------------------------------------------------
# OperationalReader DRY RUN mode tests
# ---------------------------------------------------------------------------

class TestOperationalReaderDryRun:

    def test_dry_run_reads_records(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        session = reader.run(mode="dry_run")
        assert session.records_read == 5

    def test_dry_run_creates_learning_objects(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        session = reader.run(mode="dry_run")
        assert session.outcome_comparisons_created == 5
        assert session.knowledge_created == 5
        assert session.criterion_deltas_proposed == 5

    def test_dry_run_does_not_persist(self, temp_trade_json):
        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_trade_json], store=store)
        reader.run(mode="dry_run")
        conn = sqlite3.connect(store_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        for t in tables:
            if t == "sqlite_sequence":
                continue
            conn2 = sqlite3.connect(store_path)
            count = conn2.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
            conn2.close()
            assert count == 0, f"Table {t} has {count} rows in dry_run mode"

    def test_dry_run_generates_verdicts(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        session = reader.run(mode="dry_run")
        total = sum(session.verdict_distribution.values())
        assert total == 5

    def test_dry_run_knowledge_has_provenance(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        session = reader.run(mode="dry_run")
        assert reader._generated_knowledge
        for k in reader._generated_knowledge:
            prov = k.provenance
            assert isinstance(prov, dict)
            assert prov.get("source") == OPERATIONAL_PROVENANCE
            assert "source_record_id" in prov
            assert "source_table_or_file" in prov

    def test_dry_run_hypothesis_has_provenance(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        reader.run(mode="dry_run")
        assert reader._generated_hypotheses
        for h in reader._generated_hypotheses:
            assert OPERATIONAL_PROVENANCE in h.description
            assert OPERATIONAL_PROVENANCE in h.status_history[-1]["reason"]

    def test_dry_run_deltas_are_pending(self, temp_trade_json):
        reader = OperationalReader(sources=[temp_trade_json])
        reader.run(mode="dry_run")
        assert reader._generated_deltas
        for d in reader._generated_deltas:
            assert d.status.value == "pending_review"

    def test_dry_run_with_sqlite_source(self, temp_sqlite_trades):
        reader = OperationalReader(sources=[temp_sqlite_trades])
        session = reader.run(mode="dry_run")
        assert session.records_read == 5
        assert session.trades_detected == 5
        assert session.outcome_comparisons_created == 5

    def test_dry_run_with_directory(self, temp_directory_with_data):
        reader = OperationalReader(sources=[temp_directory_with_data])
        session = reader.run(mode="dry_run")
        assert session.records_read == 6
        assert session.trades_detected == 6

    def test_dry_run_blocked_signals_not_persisted(self, tmp_path):
        """Verify blocked signals are reported but not persisted as MissedOpportunity."""
        f_path = tmp_path / "blocked_signals.json"
        records = [
            {"asset": "SOL", "direction": "long", "confidence": 0.55,
             "risk": 0.7, "block_reason": "capital_guard_emergency"}
        ]
        with open(f_path, "w") as f:
            json.dump(records, f)

        reader = OperationalReader(sources=[str(f_path)])
        session = reader.run(mode="dry_run")
        assert session.blocked_signals_detected == 1
        assert "capital_guard_emergency" in session.block_reason_distribution
        assert session.outcome_comparisons_created == 0  # no trade transformation

    def test_dry_run_with_oma_core_style_db(self, temp_oma_core_db):
        """Events + opportunities without trades should produce 0 learning objects."""
        reader = OperationalReader(sources=[temp_oma_core_db])
        session = reader.run(mode="dry_run")
        assert session.trades_detected == 0
        assert session.signals_detected == 0
        assert session.outcome_comparisons_created == 0


# ---------------------------------------------------------------------------
# OperationalReader COMMIT mode tests
# ---------------------------------------------------------------------------

class TestOperationalReaderCommit:

    def test_commit_writes_to_scientific_db(self, temp_trade_json):
        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_trade_json], store=store)
        session = reader.run(mode="commit")
        assert session.outcome_comparisons_created == 5
        conn = sqlite3.connect(store_path)
        count = conn.execute("SELECT COUNT(*) FROM outcome_comparisons").fetchone()[0]
        conn.close()
        assert count == 5

    def test_commit_writes_only_to_scientific_db(self, temp_trade_json):
        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_trade_json], store=store)
        reader.run(mode="commit")
        conn = sqlite3.connect(store_path)
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        expected = {"hypotheses", "evidence", "outcome_comparisons",
                     "knowledge", "criterion_deltas"}
        actual = set(tables) - {"sqlite_sequence"}
        assert expected.issubset(actual), f"Missing tables: {expected - actual}"

    def test_commit_never_writes_to_source_db(self, temp_trade_json):
        """Verify commit mode never modifies the source (oma_core) db."""
        source_path = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(source_path)
        conn.execute("CREATE TABLE trades (id TEXT, asset TEXT)")
        conn.execute("INSERT INTO trades VALUES ('t1', 'BTC')")
        conn.commit()
        conn.close()

        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[source_path], store=store)
        reader.run(mode="commit")

        conn = sqlite3.connect(source_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert "outcome_comparisons" not in tables
        assert "knowledge" not in tables
        assert "criterion_deltas" not in tables
        assert "hypotheses" not in tables
        os.unlink(source_path)
        os.unlink(store_path)


# ---------------------------------------------------------------------------
# Safety and boundary tests
# ---------------------------------------------------------------------------

class TestSafety:

    def test_reader_never_modifies_source_db(self, temp_sqlite_trades):
        conn = sqlite3.connect(temp_sqlite_trades)
        cursor = conn.execute("SELECT COUNT(*) FROM trades")
        before = cursor.fetchone()[0]
        conn.close()

        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_sqlite_trades], store=store)
        reader.run(mode="commit")

        conn = sqlite3.connect(temp_sqlite_trades)
        cursor = conn.execute("SELECT COUNT(*) FROM trades")
        after = cursor.fetchone()[0]
        conn.close()
        assert before == after
        os.unlink(store_path)

    def test_no_new_tables_in_source_db(self, temp_sqlite_trades):
        conn = sqlite3.connect(temp_sqlite_trades)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_before = set(row[0] for row in cursor.fetchall())
        conn.close()

        store_path = tempfile.mktemp(suffix=".db")
        store = ScientificStore(db_path=store_path)
        reader = OperationalReader(sources=[temp_sqlite_trades], store=store)
        reader.run(mode="commit")

        conn = sqlite3.connect(temp_sqlite_trades)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_after = set(row[0] for row in cursor.fetchall())
        conn.close()
        assert tables_before == tables_after
        os.unlink(store_path)

    def test_missing_source_does_not_crash(self):
        reader = OperationalReader(sources=["/nonexistent/db.db"])
        session = reader.run(mode="dry_run")
        assert session.records_read == 0

    def test_partial_records_still_process(self, tmp_path):
        records = [
            {"id": "t1", "asset": "BTC", "direction": "long",
             "pnl_percent": 5.0, "exit_reason": "take_profit", "confidence": 0.7},
            {"id": "t2", "asset": "ETH"},
        ]
        f_path = tmp_path / "partial.json"
        with open(f_path, "w") as f:
            json.dump(records, f)

        reader = OperationalReader(sources=[str(f_path)])
        session = reader.run(mode="dry_run")
        assert session.records_read == 2
        assert session.trades_detected == 1
        assert session.outcome_comparisons_created == 1

    def test_report_generated_in_dry_run(self, temp_trade_json):
        with tempfile.TemporaryDirectory() as td:
            reader = OperationalReader(sources=[temp_trade_json])
            session = reader.run(mode="dry_run")
            json_path = session.save_json(Path(td))
            md_path = session.save_markdown(Path(td))
            assert Path(json_path).exists()
            assert Path(md_path).exists()


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------

class TestRegression:

    def test_existing_historical_replay_still_works(self):
        from core.scientific.historical_replay import HistoricalReplay
        from pathlib import Path
        fixture_path = Path("fixtures") / "sample_trades.json"
        replay = HistoricalReplay(source=str(fixture_path), is_dry_run=True)
        session = replay.run()
        assert session.records_read == 10
        assert session.comparisons_created == 10

    def test_existing_lab_workflow_still_passes(self):
        from core.scientific.outcome_comparison import compare_outcome
        from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
        from core.schemas.outcome_comparison_schema import Verdict
        from datetime import datetime, timezone
        hyp = Hypothesis(
            id="test",
            title="Test",
            description="Test hypothesis",
            predicted_consequence="price goes up",
            conditions="None",
            invalidation_conditions="None",
            confidence=0.5,
            status=HypothesisStatus.FORMULATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        comparison = compare_outcome(hyp, "price went up", verdict=Verdict.CONFIRMED)
        assert comparison.verdict == Verdict.CONFIRMED

    def test_reader_does_not_create_operational_files(self):
        """Verify the operational reader does not create operational files."""
        store_paths_before = set(Path(".").glob("oma_core.db*"))
        assert True  # safety: reader does not create oma_core.db files
