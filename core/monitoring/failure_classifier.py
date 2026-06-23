from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class FailureSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FailureCategory(Enum):
    DATA_FAILURE = "data_failure"
    API_FAILURE = "api_failure"
    LOGIC_FAILURE = "logic_failure"
    RISK_FAILURE = "risk_failure"
    EXECUTION_FAILURE = "execution_failure"
    GUARD_FAILURE = "guard_failure"
    MEMORY_FAILURE = "memory_failure"
    TELEMETRY_FAILURE = "telemetry_failure"
    UNKNOWN = "unknown"


class FailureClassifier:
    """Classifies and records runtime anomalies.

    Does NOT take recovery action — only observes, classifies,
    and persists. Recovery is the responsibility of the demo
    harness or operator.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._file: Optional[Path] = None

    @property
    def filepath(self) -> Path:
        if self._file is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._file = self.output_dir / f"failures_{ts}.jsonl"
        return self._file

    @staticmethod
    def classify(exception: Exception) -> FailureCategory:
        exc_name = type(exception).__name__
        msg = str(exception).lower()
        words = set(msg.split())

        api_keywords = {"connection", "timeout", "http", "api", "rate_limit",
                        "binance", "yfinance", "request", "network"}
        data_keywords = {"ohlcv", "price", "data", "empty", "missing", "nan", "inf"}
        risk_keywords = {"drawdown", "exposure"}
        execution_keywords = {"trade", "order", "execution", "position", "size"}
        guard_keywords = {"guard", "kill", "halt", "block"}
        memory_keywords = {"memory", "store", "recall", "persist"}
        telemetry_keywords = {"telemetry", "jsonl"}

        if words & api_keywords:
            return FailureCategory.API_FAILURE
        if words & data_keywords:
            return FailureCategory.DATA_FAILURE
        if "risk" in words:
            return FailureCategory.RISK_FAILURE
        if words & execution_keywords:
            return FailureCategory.EXECUTION_FAILURE
        if words & guard_keywords:
            return FailureCategory.GUARD_FAILURE
        if words & memory_keywords:
            return FailureCategory.MEMORY_FAILURE
        if words & telemetry_keywords:
            return FailureCategory.TELEMETRY_FAILURE

        # Substring fallback for compound terms
        msg_no_punct = "".join(c if c.isalnum() or c == " " else " " for c in msg)
        compounds = {
            "rate limit": FailureCategory.API_FAILURE,
            "kill switch": FailureCategory.GUARD_FAILURE,
        }
        for phrase, cat in compounds.items():
            if phrase in msg_no_punct:
                return cat

        return FailureCategory.UNKNOWN

    @staticmethod
    def severity(exception: Exception, category: FailureCategory) -> FailureSeverity:
        if category in (FailureCategory.RISK_FAILURE, FailureCategory.GUARD_FAILURE):
            return FailureSeverity.CRITICAL
        exc_name = type(exception).__name__
        if exc_name in ("SystemExit", "KeyboardInterrupt", "MemoryError"):
            return FailureSeverity.CRITICAL
        if exc_name in ("ValueError", "TypeError", "KeyError", "IndexError"):
            return FailureSeverity.ERROR
        if exc_name in ("ConnectionError", "TimeoutError", "OSError"):
            return FailureSeverity.WARNING
        return FailureSeverity.INFO

    def record(
        self,
        exception: Exception,
        cycle_id: int = 0,
        recovery_action: str = "none",
        resolved: bool = False,
        impact: str = "unknown",
    ) -> dict[str, Any]:
        category = self.classify(exception)
        sev = self.severity(exception, category)
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": cycle_id,
            "severity": sev.value,
            "category": category.value,
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "stacktrace": traceback.format_exc(),
            "recovery_action": recovery_action,
            "resolved": resolved,
            "impact": impact,
        }
        line = json.dumps(entry, default=str) + "\n"
        with open(self.filepath, "a") as f:
            f.write(line)
        return entry

    def read_all(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for p in sorted(self.output_dir.glob("failures_*.jsonl")):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries

    def summary(self) -> dict[str, Any]:
        entries = self.read_all()
        if not entries:
            return {}
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for e in entries:
            cat = e.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            sev = e.get("severity", "info")
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {
            "total_failures": len(entries),
            "by_category": by_category,
            "by_severity": by_severity,
            "critical_count": by_severity.get("critical", 0),
            "unresolved": sum(1 for e in entries if not e.get("resolved", True)),
        }
