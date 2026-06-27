"""O.M.A.-C.O.R.E. Read-Only Operational Integration

Connects the Scientific Learning Laboratory to real operational data sources
in read-only mode so the system can learn from actual MVP history without
touching execution, runtime, or operational databases.

Safety invariants enforced at import time:
  - No write access to oma_core.db
  - No modification of operational modules
  - All writes go exclusively to scientific.db (commit mode only)
"""
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set

from core.schemas.hypothesis_schema import Hypothesis, HypothesisStatus
from core.schemas.outcome_comparison_schema import (
    OutcomeComparison, Verdict, ErrorType, ComparisonType,
)
from core.schemas.knowledge_schema import Knowledge, KnowledgeStatus
from core.schemas.criterion_delta_schema import CriterionDelta, DeltaStatus
from core.scientific.scientific_store import ScientificStore
from core.scientific.historical_replay import (
    _find_field, _normalize_direction, _determine_verdict_from_pnl,
    _determine_verdict_from_exit, _generate_hypothesis_statement,
    COMMON_TRADE_FIELDS, REPLAY_PROVENANCE,
)
from core.scientific.knowledge_lifecycle import extract_knowledge, promote_to_provisional
from core.scientific.criterion_evolution import propose_delta

REPORT_DIR = Path("_project-memory") / "operational_integration"
OPERATIONAL_PROVENANCE = "generated_from_read_only_operational_integration"

KNOWN_SOURCES = [
    "oma_core.db",
    "scientific.db",
    "oma_core.db.backup_v20",
    "_extended_demo",
    "_live_paper_gate",
    "logs",
    "_project-memory",
]

TELEMETRY_PATTERNS = ["telemetry_*.jsonl", "guard_audit_*.jsonl", "execution_audit_*.jsonl"]
REPLAY_REPORT_PATTERN = "learning_replay_*.json"


def _is_readable_sqlite(path: Path) -> bool:
    try:
        if not path.exists() or path.is_dir():
            return False
        with open(path, "rb") as f:
            header = f.read(16)
        if header != b"SQLite format 3\0":
            return False
        conn = sqlite3.connect(str(path))
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _get_sqlite_tables(path: Path) -> List[str]:
    tables = []
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception:
        pass
    return tables


def _get_sqlite_table_columns(path: Path, table: str) -> List[str]:
    columns = []
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.execute(f"SELECT * FROM \"{table}\" LIMIT 0")
        columns = [desc[0] for desc in cursor.description]
        conn.close()
    except Exception:
        pass
    return columns


def _get_table_row_count(path: Path, table: str) -> int:
    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def _detect_data_type_from_columns(columns: Set[str]) -> str:
    cols_lower = {c.lower() for c in columns}
    trade_indicators = {"pnl", "pnl_pct", "pnl_percent", "return_pct", "entry_price", "exit_price", "trade_id"}
    if trade_indicators & cols_lower and ("asset" in cols_lower or "symbol" in cols_lower):
        return "trade"
    has_signal_id = "signal_id" in cols_lower
    if has_signal_id or ("direction" in cols_lower and "confidence" in cols_lower and "asset" in cols_lower):
        return "signal"
    event_indicators = {"event_type", "source_url", "raw_content"}
    if event_indicators & cols_lower:
        return "event"
    opportunity_indicators = {"opportunity_type", "action_suggested", "asset_class"}
    if opportunity_indicators & cols_lower or ("score" in cols_lower and "conviction" in cols_lower):
        return "opportunity"
    if "cycle" in cols_lower and "timestamp" in cols_lower:
        return "telemetry"
    return "unknown"


def _detect_file_data_type(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return "unknown"
        data = json.loads(content)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        if isinstance(data, dict):
            return _detect_data_type_from_columns(set(data.keys()))
    except Exception:
        pass
    return "unknown"


def _read_operational_records(path: Path, table: Optional[str] = None, limit: int = 5000) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    suffix = path.suffix.lower()
    try:
        if suffix in (".db", ".sqlite", ".sqlite3"):
            return _read_sqlite_table(path, table, limit)
        elif suffix == ".jsonl":
            return _read_jsonl(path, limit)
        elif suffix == ".json":
            return _read_json(path)
        elif path.is_dir():
            return _read_directory(path, limit)
        else:
            return _read_json(path)
    except Exception:
        return []


def _read_sqlite_table(path: Path, table: Optional[str] = None, limit: int = 5000) -> List[Dict[str, Any]]:
    records = []
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        if table:
            cursor = conn.execute(f"SELECT * FROM \"{table}\" LIMIT ?", (limit,))
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                records.append(dict(zip(columns, row)))
        else:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for table_row in cursor.fetchall():
                t = table_row[0]
                tc = conn.execute(f"SELECT * FROM \"{t}\" LIMIT ?", (limit,))
                tcols = [desc[0] for desc in tc.description]
                for row in tc.fetchall():
                    records.append(dict(zip(tcols, row)))
        conn.close()
    except Exception:
        pass
    return records


def _read_jsonl(path: Path, limit: int = 5000) -> List[Dict[str, Any]]:
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                        if len(records) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return records


def _read_json(path: Path) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("trades", "records", "data", "results", "items", "events", "opportunities"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
    except Exception:
        pass
    return []


def _read_directory(path: Path, limit: int = 5000) -> List[Dict[str, Any]]:
    records = []
    supported = {".json", ".jsonl"}
    for f in sorted(path.iterdir()):
        if f.is_file() and f.suffix.lower() in supported:
            try:
                file_records = _read_json(f) if f.suffix.lower() == ".json" else _read_jsonl(f)
                records.extend(file_records)
                if len(records) >= limit:
                    break
            except Exception:
                continue
    return records[:limit]


def _is_trade_record(record: Dict[str, Any]) -> bool:
    keys_lower = {k.lower() for k in record.keys()}
    has_pnl = any(k in keys_lower for k in ["pnl", "pnl_pct", "pnl_percent", "return_pct", "pnl_absolute"])
    has_asset = any(k in keys_lower for k in ["asset", "symbol", "instrument", "pair"])
    return has_pnl and has_asset


def _is_signal_record(record: Dict[str, Any]) -> bool:
    keys_lower = {k.lower() for k in record.keys()}
    has_direction = any(k in keys_lower for k in ["direction", "side", "action"])
    has_confidence = "confidence" in keys_lower or "conviction" in keys_lower
    has_asset = any(k in keys_lower for k in ["asset", "symbol", "instrument", "pair"])
    return has_direction and has_confidence and has_asset


def _is_telemetry_record(record: Dict[str, Any]) -> bool:
    keys_lower = {k.lower() for k in record.keys()}
    has_cycle = "cycle" in keys_lower
    has_timestamp = "timestamp" in keys_lower
    has_events = "events_collected" in keys_lower or "events_processed" in keys_lower or "signals_generated" in keys_lower
    return has_cycle or (has_timestamp and has_events)


def _is_blocked_signal_record(record: Dict[str, Any]) -> bool:
    keys_lower = {k.lower() for k in record.keys()}
    has_block_reason = any(k in keys_lower for k in ["block_reason", "why_blocked"])
    has_asset = any(k in keys_lower for k in ["asset", "symbol", "instrument", "pair"])
    return has_block_reason and has_asset


def _is_learning_replay_record(record: Dict[str, Any]) -> bool:
    return "session_id" in record and "mode" in record and "records_read" in record


def _normalize_operational_record(record: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}
    key_map = {
        "asset": ["asset", "symbol", "instrument", "pair"],
        "direction": ["direction", "side", "action"],
        "entry_price": ["entry_price", "entry", "open_price", "entryprice"],
        "exit_price": ["exit_price", "exit", "close_price", "exitprice"],
        "entry_time": ["entry_time", "entry_at", "opened_at", "open_time", "entrytimestamp"],
        "exit_time": ["exit_time", "exit_at", "closed_at", "close_time", "exittimestamp"],
        "pnl_percent": ["pnl_percent", "pnl_pct", "return_pct", "profit_loss_pct", "return"],
        "pnl_absolute": ["pnl_absolute", "pnl", "profit_loss", "return_abs"],
        "exit_reason": ["exit_reason", "close_reason", "reason"],
        "confidence": ["confidence", "conviction", "score"],
        "signal_reason": ["signal_reason", "hypothesis_statement", "hypothesis", "reason", "entry_reason", "rationale", "title"],
    }
    for target, source_keys in key_map.items():
        for sk in source_keys:
            if sk in record and record[sk] is not None:
                normalized[target] = record[sk]
                break
    for k, v in record.items():
        if k not in normalized:
            normalized[k] = v
    return normalized


def _auto_discover_sources(target_dir: str = ".") -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    base = Path(target_dir)
    for name in KNOWN_SOURCES:
        path = base / name
        if path.exists():
            if path.is_dir():
                found.append((str(path.resolve()), "directory"))
            elif _is_readable_sqlite(path):
                found.append((str(path.resolve()), "sqlite"))
            elif path.suffix == ".json":
                found.append((str(path.resolve()), "json"))
            elif path.suffix == ".jsonl":
                found.append((str(path.resolve()), "jsonl"))
    telemetry_dirs = [base / "_extended_demo", base / "_live_paper_gate", base / "logs", base / "_project-memory"]
    for td in telemetry_dirs:
        if td.exists() and td.is_dir():
            for pat in TELEMETRY_PATTERNS:
                for f in td.glob(pat):
                    found.append((str(f.resolve()), "jsonl"))
    replay_dir = base / "_project-memory" / "learning_replay"
    if replay_dir.exists():
        for f in replay_dir.glob(REPLAY_REPORT_PATTERN):
            found.append((str(f.resolve()), "json"))
    return found


def _read_operational_source(path_str: str, source_type: str) -> Dict[str, Any]:
    result = {
        "path": path_str,
        "source_type": source_type,
        "exists": Path(path_str).exists(),
        "readable": False,
        "tables_or_files": [],
        "row_count": 0,
        "detected_data_types": {},
        "sample_records": [],
        "error": None,
    }
    path = Path(path_str)
    if not path.exists():
        result["error"] = "Path does not exist"
        return result
    try:
        if source_type == "sqlite":
            tables = _get_sqlite_tables(path)
            result["tables_or_files"] = tables
            result["readable"] = len(tables) > 0
            for table in tables:
                columns = _get_sqlite_table_columns(path, table)
                row_count = _get_table_row_count(path, table)
                dt = _detect_data_type_from_columns(set(columns))
                result["detected_data_types"][table] = {"type": dt, "columns": columns, "rows": row_count}
                result["row_count"] += row_count
        elif source_type in ("json", "jsonl"):
            result["tables_or_files"] = [path.name]
            result["readable"] = True
            dt = _detect_file_data_type(path)
            sample = _read_operational_records(path, limit=5)
            result["detected_data_types"][path.name] = {"type": dt, "records": len(sample)}
            result["row_count"] = len(_read_operational_records(path, limit=10000))
        elif source_type == "directory":
            files = sorted([f.name for f in path.iterdir() if f.is_file()])
            result["tables_or_files"] = files
            result["readable"] = True
            for fname in files:
                fp = path / fname
                if fp.suffix.lower() in (".json", ".jsonl"):
                    dt = _detect_file_data_type(fp)
                    sample = _read_operational_records(fp, limit=5)
                    result["detected_data_types"][fname] = {"type": dt, "records": len(sample)}
    except Exception as e:
        result["error"] = str(e)
    return result


class OperationalDataInventory:
    """Report of operational data sources found, inspected, and categorized.

    Produced in AUDIT mode. No learning objects are created.
    """

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.sources_found: List[Dict[str, Any]] = []
        self.total_records = 0
        self.trades_found = 0
        self.signals_found = 0
        self.events_found = 0
        self.opportunities_found = 0
        self.telemetry_records_found = 0
        self.blocked_signals_found = 0
        self.learning_replay_sessions_found = 0
        self.readable_sources = 0
        self.empty_sources = 0
        self.inaccessible_sources = 0
        self.missing_sources: List[str] = []
        self.warnings: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "sources_found": self.sources_found,
            "total_records": self.total_records,
            "trades_found": self.trades_found,
            "signals_found": self.signals_found,
            "events_found": self.events_found,
            "opportunities_found": self.opportunities_found,
            "telemetry_records_found": self.telemetry_records_found,
            "blocked_signals_found": self.blocked_signals_found,
            "learning_replay_sessions_found": self.learning_replay_sessions_found,
            "readable_sources": self.readable_sources,
            "empty_sources": self.empty_sources,
            "inaccessible_sources": self.inaccessible_sources,
            "missing_sources": self.missing_sources,
            "warnings": self.warnings,
        }

    def save(self, report_dir: Optional[Path] = None) -> Path:
        out_dir = report_dir or REPORT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"operational_inventory_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    def print_summary(self) -> None:
        src_count = sum(
            1 for s in self.sources_found if not s.get("error")
        )
        print(f"\n{'=' * 55}")
        print(f"  Operational Data Inventory")
        print(f"{'=' * 55}")
        print(f"  Session ID:       {self.session_id[:16]}...")
        print(f"  Sources found:    {src_count}")
        print(f"  Total records:    {self.total_records}")
        print(f"  Trades:           {self.trades_found}")
        print(f"  Signals:          {self.signals_found}")
        print(f"  Events:           {self.events_found}")
        print(f"  Opportunities:    {self.opportunities_found}")
        print(f"  Telemetry:        {self.telemetry_records_found}")
        print(f"  Blocked signals:  {self.blocked_signals_found}")
        print(f"  Replay sessions:  {self.learning_replay_sessions_found}")
        if self.warnings:
            print(f"\n  Warnings:")
            for w in self.warnings:
                print(f"    {w}")
        print(f"{'=' * 55}\n")


class OperationalLearningSession:
    """Summary of one operational read-and-transform session."""

    def __init__(self, mode: str):
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.mode = mode
        self.records_read = 0
        self.trades_detected = 0
        self.signals_detected = 0
        self.blocked_signals_detected = 0
        self.telemetry_records_detected = 0
        self.learning_replay_sessions_found = 0
        self.records_transformed = 0
        self.records_skipped = 0
        self.outcome_comparisons_created = 0
        self.knowledge_created = 0
        self.criterion_deltas_proposed = 0
        self.verdict_distribution: Dict[str, int] = {}
        self.error_type_distribution: Dict[str, int] = {}
        self.block_reason_distribution: Dict[str, int] = {}
        self.confidence_distribution: Dict[str, int] = {
            "0.0-0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-1.0": 0,
        }
        self.warnings: List[str] = []
        self.limitations: List[str] = []
        self.recommended_next_action: str = "Review operational integration report and assess readiness for Stage 10."

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "records_read": self.records_read,
            "trades_detected": self.trades_detected,
            "signals_detected": self.signals_detected,
            "blocked_signals_detected": self.blocked_signals_detected,
            "telemetry_records_detected": self.telemetry_records_detected,
            "learning_replay_sessions_found": self.learning_replay_sessions_found,
            "records_transformed": self.records_transformed,
            "records_skipped": self.records_skipped,
            "outcome_comparisons_created": self.outcome_comparisons_created,
            "knowledge_created": self.knowledge_created,
            "criterion_deltas_proposed": self.criterion_deltas_proposed,
            "verdict_distribution": self.verdict_distribution,
            "error_type_distribution": self.error_type_distribution,
            "block_reason_distribution": self.block_reason_distribution,
            "confidence_distribution": self.confidence_distribution,
            "warnings": self.warnings,
            "limitations": self.limitations,
            "recommended_next_action": self.recommended_next_action,
        }

    def save_json(self, report_dir: Optional[Path] = None) -> Path:
        out_dir = report_dir or REPORT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"operational_learning_session_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    def save_markdown(self, report_dir: Optional[Path] = None) -> Path:
        out_dir = report_dir or REPORT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"operational_learning_session_{ts}.md"
        lines = [
            f"# Operational Learning Session Report",
            f"",
            f"**Session ID**: `{self.session_id[:16]}`",
            f"**Timestamp**: {self.timestamp}",
            f"**Mode**: {self.mode.upper()}",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Records Read | {self.records_read} |",
            f"| Trades Detected | {self.trades_detected} |",
            f"| Signals Detected | {self.signals_detected} |",
            f"| Blocked Signals | {self.blocked_signals_detected} |",
            f"| Telemetry Records | {self.telemetry_records_detected} |",
            f"| Records Transformed | {self.records_transformed} |",
            f"| Records Skipped | {self.records_skipped} |",
            f"| Outcome Comparisons | {self.outcome_comparisons_created} |",
            f"| Knowledge Items | {self.knowledge_created} |",
            f"| Criterion Deltas | {self.criterion_deltas_proposed} |",
            f"",
            f"## Verdict Distribution",
            f"",
        ]
        for v, c in sorted(self.verdict_distribution.items()):
            lines.append(f"- {v}: {c}")
        if self.warnings:
            lines.extend(["", "## Warnings", ""])
            for w in self.warnings:
                lines.append(f"- {w}")
        if self.limitations:
            lines.extend(["", "## Limitations", ""])
            for l in self.limitations:
                lines.append(f"- {l}")
        lines.extend(["", "---", "**Recommended Next Action**: " + self.recommended_next_action])
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path

    def print_summary(self) -> None:
        print(f"\n{'=' * 55}")
        print(f"  Operational Learning Session")
        print(f"{'=' * 55}")
        print(f"  Session ID:      {self.session_id[:16]}...")
        print(f"  Mode:            {self.mode.upper()}")
        print(f"  Records read:    {self.records_read}")
        print(f"  Transformed:     {self.records_transformed}")
        print(f"  Skipped:         {self.records_skipped}")
        print(f"  Comparisons:     {self.outcome_comparisons_created}")
        print(f"  Knowledge:       {self.knowledge_created}")
        print(f"  Deltas:          {self.criterion_deltas_proposed}")
        if self.verdict_distribution:
            print(f"\n  Verdict Distribution:")
            for v, c in sorted(self.verdict_distribution.items()):
                print(f"    {v:20s}: {c}")
        if self.warnings:
            print(f"\n  Warnings:")
            for w in self.warnings:
                print(f"    {w}")
        if self.limitations:
            print(f"\n  Limitations:")
            for l in self.limitations:
                print(f"    {l}")
        print(f"\n  -> {self.recommended_next_action}")
        print(f"{'=' * 55}\n")


class OperationalReader:
    """Main engine for read-only operational integration.

    Modes:
      AUDIT   — Inspect sources, no transformations, no DB writes.
      DRY_RUN — Read + transform in-memory objects, no DB writes.
      COMMIT  — Read + transform + write learning objects to scientific.db.

    Safety: Never writes to oma_core.db. Never modifies operational modules.
    """

    def __init__(
        self,
        sources: Optional[List[str]] = None,
        store: Optional[ScientificStore] = None,
        limit: int = 5000,
    ):
        self.sources = sources or []
        self.store = store or ScientificStore()
        self.limit = limit
        self.inventory: Optional[OperationalDataInventory] = None
        self.session: Optional[OperationalLearningSession] = None
        self._generated_hypotheses: List[Hypothesis] = []
        self._generated_comparisons: List[OutcomeComparison] = []
        self._generated_knowledge: List[Knowledge] = []
        self._generated_deltas: List[CriterionDelta] = []

    def add_source(self, path: str) -> None:
        if path not in self.sources:
            self.sources.append(path)

    def auto_discover(self) -> List[str]:
        discovered = _auto_discover_sources()
        for path_str, _ in discovered:
            if path_str not in self.sources:
                self.sources.append(path_str)
        return [s[0] for s in discovered]

    def run_audit(self) -> OperationalDataInventory:
        inventory = OperationalDataInventory()
        for source_path in self.sources:
            path = Path(source_path)
            if not path.exists():
                inventory.missing_sources.append(source_path)
                inventory.warnings.append(f"Source not found: {source_path}")
                continue
            st = "unknown"
            if path.is_dir():
                st = "directory"
            elif _is_readable_sqlite(path):
                st = "sqlite"
            elif path.suffix == ".jsonl":
                st = "jsonl"
            elif path.suffix == ".json":
                st = "json"
            source_info = _read_operational_source(source_path, st)
            inventory.sources_found.append(source_info)
            if source_info.get("error"):
                inventory.inaccessible_sources += 1
                inventory.warnings.append(f"Cannot read {source_path}: {source_info['error']}")
                continue
            if source_info["row_count"] == 0:
                inventory.empty_sources += 1
            else:
                inventory.readable_sources += 1
            inventory.total_records += source_info["row_count"]
            for table_or_file, info in source_info.get("detected_data_types", {}).items():
                dtype = info.get("type", "unknown")
                count = info.get("rows", info.get("records", 0))
                if dtype == "trade":
                    inventory.trades_found += count
                elif dtype == "signal":
                    inventory.signals_found += count
                elif dtype == "event":
                    inventory.events_found += count
                elif dtype == "opportunity":
                    inventory.opportunities_found += count
                elif dtype == "telemetry":
                    inventory.telemetry_records_found += count
        self.inventory = inventory
        return inventory

    def run(self, mode: str = "dry_run") -> OperationalLearningSession:
        if mode not in ("dry_run", "commit"):
            raise ValueError(f"Invalid mode: {mode}. Use 'dry_run' or 'commit'.")
        if self.inventory is None:
            self.run_audit()
        self._generated_hypotheses = []
        self._generated_comparisons = []
        self._generated_knowledge = []
        self._generated_deltas = []
        session = OperationalLearningSession(mode=mode)
        for source_info in (self.inventory.sources_found if self.inventory else []):
            if source_info.get("error"):
                continue
            sp = source_info["path"]
            st = source_info["source_type"]
            if st == "sqlite" and source_info.get("tables_or_files"):
                for table, info in source_info.get("detected_data_types", {}).items():
                    if info.get("type") in ("trade", "signal", "opportunity", "event"):
                        recs = _read_sqlite_table(Path(sp), table, self.limit)
                        for rec in recs:
                            self._process_record(rec, session, sp, table)
            elif st in ("json", "jsonl"):
                recs = _read_operational_records(Path(sp), limit=self.limit)
                for rec in recs:
                    self._process_record(rec, session, sp, Path(sp).name)
            elif st == "directory":
                recs = _read_directory(Path(sp), self.limit)
                for rec in recs:
                    self._process_record(rec, session, sp, Path(sp).name)
        self.session = session
        if mode == "commit":
            self._commit_to_store()
        return session

    def _process_record(
        self,
        record: Dict[str, Any],
        session: OperationalLearningSession,
        source_path: str,
        source_table: str,
    ) -> None:
        session.records_read += 1
        if _is_learning_replay_record(record):
            session.learning_replay_sessions_found += 1
            session.records_skipped += 1
            return
        if _is_trade_record(record):
            session.trades_detected += 1
            self._transform_trade_to_learning(record, session, source_path, source_table)
        elif _is_blocked_signal_record(record):
            session.blocked_signals_detected += 1
            self._record_blocked_signal(record, session, source_path, source_table)
        elif _is_signal_record(record):
            session.signals_detected += 1
            session.records_skipped += 1
        elif _is_telemetry_record(record):
            session.telemetry_records_detected += 1
        else:
            session.records_skipped += 1

    def _create_hypothesis(self, record: Dict[str, Any], source_path: str, source_table: str) -> Hypothesis:
        record_id = str(record.get("id", record.get("trade_id", "unknown")))

        asset = _find_field(record, COMMON_TRADE_FIELDS["asset"]) or "unknown_asset"
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"])) or "unknown"
        confidence = _find_field(record, COMMON_TRADE_FIELDS["confidence"])
        confidence = max(0.3, min(0.7, float(confidence))) if confidence is not None else 0.5
        statement = _generate_hypothesis_statement(record)
        now = datetime.now(timezone.utc)

        return Hypothesis(
            id=str(uuid.uuid4()),
            title=f"Operational: {direction} {asset}",
            description=(
                f"Hypothesis generated from read-only operational integration. "
                f"Original record: {record_id}. "
                f"Source: {source_table} @ {source_path}. "
                f"Provenance: {OPERATIONAL_PROVENANCE}"
            ),
            predicted_consequence=statement,
            conditions="Operational integration — market conditions from source data",
            invalidation_conditions="Outcome contradicts predicted direction",
            confidence=confidence,
            status=HypothesisStatus.FORMULATED,
            created_at=now,
            updated_at=now,
            status_history=[{
                "from_status": "none",
                "to_status": "formulated",
                "timestamp": now.isoformat(),
                "reason": f"Generated by read-only operational integration. {OPERATIONAL_PROVENANCE}",
            }],
        )

    def _compare_outcome(self, hypothesis: Hypothesis, record: Dict[str, Any]) -> OutcomeComparison:
        pnl_pct = _find_field(record, COMMON_TRADE_FIELDS["pnl_percent"])
        exit_reason = _find_field(record, COMMON_TRADE_FIELDS["exit_reason"])
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"]))
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
            tolerance_applied={"replay": True, "method": "pnl_based", "source": OPERATIONAL_PROVENANCE},
            knowledge_triggered=True,
        )

    def _extract_knowledge(self, comparison: OutcomeComparison, record: Dict[str, Any]) -> Knowledge:
        asset = _find_field(record, COMMON_TRADE_FIELDS["asset"]) or "unknown_asset"
        direction = _normalize_direction(_find_field(record, COMMON_TRADE_FIELDS["direction"])) or "unknown"
        verdict = comparison.verdict.value

        statement = (
            f"Operational integration suggests {asset} {direction} hypotheses "
            f"produced {verdict} outcomes under available trade data. "
            f"Provenance: {OPERATIONAL_PROVENANCE}."
        )

        knowledge = extract_knowledge(
            statement=statement,
            hypothesis_ids=[comparison.hypothesis_id],
            outcome_ids=[comparison.id],
            evidence_summary=f"Verdict: {verdict}. PnL and exit data from operational source.",
            conditions="Operational integration — market conditions from source data",
            scope="general",
            time_horizon="unknown",
            confidence=0.3,
        )

        knowledge.id = str(uuid.uuid4())
        knowledge.provenance = {
            "source": OPERATIONAL_PROVENANCE,
            "source_record_id": str(record.get("id", record.get("trade_id", "unknown"))),
            "source_table_or_file": record.get("_source_table", "unknown"),
            "source_path": record.get("_source_path", "unknown"),
            "hypothesis_ids": [comparison.hypothesis_id],
            "outcome_ids": [comparison.id],
        }

        promote_to_provisional(knowledge, reason="Extracted during read-only operational integration")
        return knowledge

    def _propose_delta(self, knowledge: Knowledge, comparison: OutcomeComparison, record: Dict[str, Any]) -> CriterionDelta:
        delta = propose_delta(
            knowledge_ids=[knowledge.id],
            hypothesis_ids=[comparison.hypothesis_id],
            outcome_ids=[comparison.id],
            dimension="knowledge_yield",
            change=(
                f"Operational integration generated knowledge from {comparison.verdict.value} outcome. "
                f"Review knowledge quality before adjusting evaluation criteria."
            ),
            confidence=0.3,
            proposed_by="Read-Only Operational Integration",
        )
        delta.id = str(uuid.uuid4())
        delta.source_evidence = {
            "knowledge_ids": [knowledge.id],
            "hypothesis_ids": [comparison.hypothesis_id],
            "outcome_ids": [comparison.id],
        }
        return delta

    def _transform_trade_to_learning(
        self,
        record: Dict[str, Any],
        session: OperationalLearningSession,
        source_path: str,
        source_table: str,
    ) -> None:
        normalized = _normalize_operational_record(record)
        record_id = str(record.get("id", record.get("trade_id", str(uuid.uuid4()))))

        try:
            normalized["_source_path"] = source_path
            normalized["_source_table"] = source_table

            hyp = self._create_hypothesis(normalized, source_path, source_table)
            comparison = self._compare_outcome(hyp, normalized)
            knowledge = self._extract_knowledge(comparison, normalized)
            delta = self._propose_delta(knowledge, comparison, normalized)

            self._generated_hypotheses.append(hyp)
            self._generated_comparisons.append(comparison)
            self._generated_knowledge.append(knowledge)
            self._generated_deltas.append(delta)

            session.records_transformed += 1
            session.outcome_comparisons_created += 1
            session.knowledge_created += 1
            session.criterion_deltas_proposed += 1
            session.record_verdict(comparison.verdict)
            session.record_error_type(comparison.error_type)
            session.record_confidence(comparison.comparison_confidence)
        except Exception as e:
            session.warnings.append(f"Failed to transform trade {record_id}: {e}")
            session.records_skipped += 1

    def _record_blocked_signal(
        self,
        record: Dict[str, Any],
        session: OperationalLearningSession,
        source_path: str,
        source_table: str,
    ) -> None:
        block_reason = record.get("block_reason", record.get("why_blocked", "unknown"))
        if block_reason:
            session.block_reason_distribution[block_reason] = (
                session.block_reason_distribution.get(block_reason, 0) + 1
            )

    def _commit_to_store(self) -> None:
        for hyp in self._generated_hypotheses:
            stored = self.store.create_hypothesis(
                title=hyp.title,
                description=hyp.description,
                predicted_consequence=hyp.predicted_consequence,
                conditions=hyp.conditions,
                invalidation_conditions=hyp.invalidation_conditions,
                confidence=hyp.confidence,
            )
            for comp in self._generated_comparisons:
                if comp.hypothesis_id == hyp.id:
                    comp.hypothesis_id = stored.id
            for kn in self._generated_knowledge:
                if hyp.id in kn.hypothesis_ids:
                    idx = kn.hypothesis_ids.index(hyp.id)
                    kn.hypothesis_ids[idx] = stored.id
                    kn.provenance["hypothesis_ids"] = [stored.id]
            for dl in self._generated_deltas:
                se = dl.source_evidence
                if "hypothesis_ids" in se and hyp.id in se["hypothesis_ids"]:
                    idx = se["hypothesis_ids"].index(hyp.id)
                    se["hypothesis_ids"][idx] = stored.id

        for comp in self._generated_comparisons:
            self.store.create_outcome_comparison(comp)
        for kn in self._generated_knowledge:
            self.store.create_knowledge(kn)
        for dl in self._generated_deltas:
            self.store.create_criterion_delta(dl)
