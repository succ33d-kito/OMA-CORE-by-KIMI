"""Tests for the FailureClassifier — no live API dependencies."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from core.monitoring.failure_classifier import (
    FailureClassifier, FailureCategory, FailureSeverity,
)


class TestFailureClassification:
    def test_classify_api_failure(self):
        cat = FailureClassifier.classify(ConnectionError("Binance API timeout"))
        assert cat == FailureCategory.API_FAILURE

    def test_classify_api_failure_http(self):
        cat = FailureClassifier.classify(TimeoutError("HTTP request to binance.com failed"))
        assert cat == FailureCategory.API_FAILURE

    def test_classify_data_failure(self):
        cat = FailureClassifier.classify(ValueError("Empty OHLCV data"))
        assert cat == FailureCategory.DATA_FAILURE

    def test_classify_data_failure_price(self):
        cat = FailureClassifier.classify(KeyError("Missing price data"))
        assert cat == FailureCategory.DATA_FAILURE

    def test_classify_risk_failure(self):
        cat = FailureClassifier.classify(RuntimeError("Drawdown exceeded risk limit"))
        assert cat == FailureCategory.RISK_FAILURE

    def test_classify_execution_failure(self):
        cat = FailureClassifier.classify(RuntimeError("Trade execution failed"))
        assert cat == FailureCategory.EXECUTION_FAILURE

    def test_classify_guard_failure(self):
        cat = FailureClassifier.classify(RuntimeError("Guard kill switch blocked"))
        assert cat == FailureCategory.GUARD_FAILURE

    def test_classify_memory_failure(self):
        cat = FailureClassifier.classify(RuntimeError("Memory store failed"))
        assert cat == FailureCategory.MEMORY_FAILURE

    def test_classify_telemetry_failure(self):
        cat = FailureClassifier.classify(PermissionError("Cannot write telemetry JSONL"))
        assert cat == FailureCategory.TELEMETRY_FAILURE

    def test_classify_unknown(self):
        cat = FailureClassifier.classify(ArithmeticError("Division by zero"))
        assert cat == FailureCategory.UNKNOWN


class TestFailureSeverity:
    def test_risk_is_critical(self):
        sev = FailureClassifier.severity(
            RuntimeError("Risk limit"),
            FailureCategory.RISK_FAILURE)
        assert sev == FailureSeverity.CRITICAL

    def test_guard_is_critical(self):
        sev = FailureClassifier.severity(
            RuntimeError("Guard blocked"),
            FailureCategory.GUARD_FAILURE)
        assert sev == FailureSeverity.CRITICAL

    def test_system_exit_is_critical(self):
        sev = FailureClassifier.severity(
            SystemExit(1), FailureCategory.UNKNOWN)
        assert sev == FailureSeverity.CRITICAL

    def test_value_error_is_error(self):
        sev = FailureClassifier.severity(
            ValueError("bad value"), FailureCategory.LOGIC_FAILURE)
        assert sev == FailureSeverity.ERROR

    def test_connection_error_is_warning(self):
        sev = FailureClassifier.severity(
            ConnectionError("timeout"), FailureCategory.API_FAILURE)
        assert sev == FailureSeverity.WARNING


class TestFailureClassifierFileIO:
    def test_record_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc = FailureClassifier(tmp)
            exc = ValueError("logic failure in signal processing")
            entry = fc.record(exc, cycle_id=42, resolved=False, impact="test")

            assert entry["cycle_id"] == 42
            assert entry["category"] == "unknown"
            assert entry["severity"] == "error"
            assert entry["exception_type"] == "ValueError"
            assert entry["message"] == "logic failure in signal processing"
            assert not entry["resolved"]
            assert entry["impact"] == "test"

            all_entries = fc.read_all()
            assert len(all_entries) == 1
            assert all_entries[0]["cycle_id"] == 42

    def test_multiple_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc = FailureClassifier(tmp)
            fc.record(ValueError("err1"), cycle_id=1)
            fc.record(ConnectionError("err2"), cycle_id=2)
            fc.record(RuntimeError("risk violation"), cycle_id=3)
            all_e = fc.read_all()
            assert len(all_e) == 3

    def test_summary_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc = FailureClassifier(tmp)
            s = fc.summary()
            assert s == {}

    def test_summary_with_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc = FailureClassifier(tmp)
            fc.record(ValueError("v1"), cycle_id=1, resolved=True)
            fc.record(ConnectionError("c1"), cycle_id=2, resolved=False)
            fc.record(SystemExit(1), cycle_id=3, resolved=False)
            s = fc.summary()
            assert s["total_failures"] == 3
            assert s["unresolved"] == 2
            assert s["by_severity"]["error"] == 1
            assert s["by_severity"]["critical"] == 1
            assert s["by_severity"]["warning"] == 1

    def test_filepath_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc1 = FailureClassifier(tmp)
            fc1.record(ValueError("test"), cycle_id=1)
            path = fc1.filepath
            assert os.path.exists(path)

            fc2 = FailureClassifier(tmp)
            entries = fc2.read_all()
            assert len(entries) == 1

    def test_record_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            fc = FailureClassifier(tmp)
            entry = fc.record(ValueError("test"), cycle_id=5)
            assert isinstance(entry, dict)
            assert "timestamp" in entry
            assert "stacktrace" in entry
