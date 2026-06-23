from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class TelemetryRecorder:
    """Append-only JSONL telemetry for long-running processes.

    Each cycle records a single JSON line. Safe for concurrent
    appending. Never rewrites or truncates.
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._file: Optional[Path] = None

    @property
    def filepath(self) -> Path:
        if self._file is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._file = self.output_dir / f"telemetry_{ts}.jsonl"
        return self._file

    def record(self, data: dict[str, Any]) -> None:
        data["_recorded_at"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(data, default=str) + "\n"
        with open(self.filepath, "a") as f:
            f.write(line)

    def read_all(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for p in sorted(self.output_dir.glob("telemetry_*.jsonl")):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        return entries

    def read_recent(self, n: int = 100) -> list[dict[str, Any]]:
        entries = self.read_all()
        return entries[-n:]

    def summary(self) -> dict[str, Any]:
        entries = self.read_all()
        if not entries:
            return {}
        return {
            "total_cycles": len(entries),
            "first_cycle": entries[0].get("timestamp", ""),
            "last_cycle": entries[-1].get("timestamp", ""),
            "total_events": sum(e.get("events_collected", 0) for e in entries),
            "total_signals": sum(e.get("signals_generated", 0) for e in entries),
            "total_trades_opened": sum(e.get("trades_opened", 0) for e in entries),
            "total_trades_closed": sum(e.get("trades_closed", 0) for e in entries),
            "total_errors": sum(e.get("runtime_errors", 0) for e in entries),
            "total_guard_blocks": sum(e.get("guard_blocks", 0) for e in entries),
            "total_execution_blocks": sum(e.get("execution_blocks", 0) for e in entries),
        }


class GuardAuditRecorder:
    """Append-only JSONL for every guard intervention."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._file: Optional[Path] = None

    @property
    def filepath(self) -> Path:
        if self._file is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._file = self.output_dir / f"guard_audit_{ts}.jsonl"
        return self._file

    def record(self, entry: dict[str, Any]) -> None:
        entry["_recorded_at"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(entry, default=str) + "\n"
        with open(self.filepath, "a") as f:
            f.write(line)

    def read_all(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for p in sorted(self.output_dir.glob("guard_audit_*.jsonl")):
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
        blockers = [e for e in entries if "block" in e.get("block_reason", "").lower()]
        size_reductions = [e for e in entries if e.get("original_size", 1) > e.get("adjusted_size", 0)]
        return {
            "total_interventions": len(entries),
            "total_blocked": len(blockers),
            "total_size_reductions": len(size_reductions),
            "guard_sources": list({e.get("guard_source", "unknown") for e in entries}),
        }
