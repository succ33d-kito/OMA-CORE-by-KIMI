from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    check_name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


class HealthMonitor:
    """Non-invasive health monitor.

    Observes system state and reports health without modifying any
    component behavior. Each check returns a CheckResult with status
    and message. The overall health is the most severe status across
    all checks.
    """

    def __init__(self) -> None:
        self._checks: dict[str, Any] = {}

    def register_component(self, name: str, component: Any) -> None:
        self._checks[name] = component

    def check_process_alive(self) -> CheckResult:
        return CheckResult(
            check_name="process_alive",
            status=HealthStatus.HEALTHY,
            message="Process is running",
        )

    def check_equity_sanity(self, equity: float, initial_capital: float) -> CheckResult:
        if equity <= 0:
            return CheckResult(
                check_name="equity_sanity",
                status=HealthStatus.CRITICAL,
                message=f"Equity {equity:.2f} is non-positive",
                details={"equity": equity, "initial_capital": initial_capital},
            )
        if equity > initial_capital * 10:
            return CheckResult(
                check_name="equity_sanity",
                status=HealthStatus.CRITICAL,
                message=f"Equity {equity:.2f} exceeds 10x initial capital {initial_capital:.2f}",
                details={"equity": equity, "initial_capital": initial_capital},
            )
        return CheckResult(
            check_name="equity_sanity",
            status=HealthStatus.HEALTHY,
            message=f"Equity {equity:.2f} is reasonable",
            details={"equity": equity, "initial_capital": initial_capital},
        )

    def check_capital_guard_mode(self, guard_mode: Any) -> CheckResult:
        mode_str = str(guard_mode)
        if "halt" in mode_str.lower():
            return CheckResult(
                check_name="capital_guard_mode",
                status=HealthStatus.CRITICAL,
                message=f"CapitalGuard in HALT mode",
                details={"guard_mode": mode_str},
            )
        if "emergency" in mode_str.lower():
            return CheckResult(
                check_name="capital_guard_mode",
                status=HealthStatus.CRITICAL,
                message=f"CapitalGuard in EMERGENCY mode",
                details={"guard_mode": mode_str},
            )
        if "caution" in mode_str.lower():
            return CheckResult(
                check_name="capital_guard_mode",
                status=HealthStatus.DEGRADED,
                message=f"CapitalGuard in CAUTION mode",
                details={"guard_mode": mode_str},
            )
        return CheckResult(
            check_name="capital_guard_mode",
            status=HealthStatus.HEALTHY,
            message=f"CapitalGuard mode is {mode_str}",
            details={"guard_mode": mode_str},
        )

    def check_crash_mode(self, crash_mode: Any) -> CheckResult:
        mode_str = str(crash_mode)
        if "panic" in mode_str.lower():
            return CheckResult(
                check_name="crash_mode",
                status=HealthStatus.CRITICAL,
                message=f"CrashDetector in PANIC mode",
                details={"crash_mode": mode_str},
            )
        if "emergency" in mode_str.lower():
            return CheckResult(
                check_name="crash_mode",
                status=HealthStatus.CRITICAL,
                message=f"CrashDetector in EMERGENCY mode",
                details={"crash_mode": mode_str},
            )
        if "warning" in mode_str.lower():
            return CheckResult(
                check_name="crash_mode",
                status=HealthStatus.DEGRADED,
                message=f"CrashDetector in WARNING mode",
                details={"crash_mode": mode_str},
            )
        return CheckResult(
            check_name="crash_mode",
            status=HealthStatus.HEALTHY,
            message=f"Crash mode is {mode_str}",
            details={"crash_mode": mode_str},
        )

    def check_open_positions(
        self,
        trades: list[Any],
        max_holding_hours: float = 72.0,
    ) -> CheckResult:
        stale = []
        for t in trades:
            status = getattr(t, "status", None)
            if str(status) in ("PENDING", "OPEN") or getattr(t, "entry_time", None) is not None:
                entry = getattr(t, "entry_time", None)
                if entry:
                    age = (datetime.now(timezone.utc) - entry).total_seconds() / 3600
                    if age > max_holding_hours:
                        stale.append({
                            "id": str(getattr(t, "id", None)),
                            "age_hours": round(age, 1),
                        })
        if stale:
            return CheckResult(
                check_name="open_positions",
                status=HealthStatus.CRITICAL,
                message=f"Found {len(stale)} stale open positions beyond {max_holding_hours}h",
                details={"stale_positions": stale},
            )
        return CheckResult(
            check_name="open_positions",
            status=HealthStatus.HEALTHY,
            message=f"No stale open positions",
            details={"open_count": len(trades)},
        )

    def check_negative_position_sizes(self, trades: list[Any]) -> CheckResult:
        negative = []
        for t in trades:
            size = getattr(t, "size", 0) or 0
            if size < 0:
                negative.append({"id": str(getattr(t, "id", None)), "size": size})
        if negative:
            return CheckResult(
                check_name="position_sizes",
                status=HealthStatus.CRITICAL,
                message=f"Found {len(negative)} negative position sizes",
                details={"negative_positions": negative},
            )
        return CheckResult(
            check_name="position_sizes",
            status=HealthStatus.HEALTHY,
            message="All position sizes non-negative",
        )

    def check_trade_consistency(self, trades: list[Any]) -> CheckResult:
        inconsistent = []
        for t in trades:
            status = getattr(t, "status", None)
            pnl = getattr(t, "pnl_absolute", None)
            if str(status) in ("CLOSED",) and pnl is None:
                inconsistent.append({"id": str(getattr(t, "id", None)), "reason": "closed trade missing PnL"})
            if str(status) in ("OPEN", "PENDING"):
                entry = getattr(t, "entry_price_executed", None)
                if entry is None:
                    inconsistent.append({
                        "id": str(getattr(t, "id", None)),
                        "reason": "open trade missing entry price",
                    })
        if inconsistent:
            return CheckResult(
                check_name="trade_consistency",
                status=HealthStatus.CRITICAL,
                message=f"Found {len(inconsistent)} inconsistent trades",
                details={"inconsistent_trades": inconsistent},
            )
        return CheckResult(
            check_name="trade_consistency",
            status=HealthStatus.HEALTHY,
            message="All trades consistent",
        )

    def check_missing_price_data(self, engine: Any, symbols: list[str]) -> CheckResult:
        missing = []
        for sym in symbols:
            prices = getattr(engine, "current_prices", None) or getattr(engine, "_price_history", None)
            if prices is None:
                missing.append(sym)
        if missing:
            return CheckResult(
                check_name="price_data",
                status=HealthStatus.DEGRADED,
                message=f"Missing price data for {missing}",
                details={"missing_symbols": missing},
            )
        return CheckResult(
            check_name="price_data",
            status=HealthStatus.HEALTHY,
            message="All price data available",
        )

    def check_repeated_cycles(
        self,
        recent_telemetry: list[dict[str, Any]],
        threshold: int = 3,
    ) -> CheckResult:
        if len(recent_telemetry) < threshold:
            return CheckResult(
                check_name="cycle_diversity",
                status=HealthStatus.HEALTHY,
                message="Too few cycles to check",
            )
        recent = recent_telemetry[-threshold:]
        events_set = set(r.get("events_collected", 0) for r in recent)
        signals_set = set(r.get("signals_generated", 0) for r in recent)
        if len(events_set) == 1 and len(signals_set) == 1:
            return CheckResult(
                check_name="cycle_diversity",
                status=HealthStatus.DEGRADED,
                message=f"Last {threshold} cycles have identical event/signal counts",
                details={"recent_telemetry": recent},
            )
        return CheckResult(
            check_name="cycle_diversity",
            status=HealthStatus.HEALTHY,
            message="Cycles show expected diversity",
        )

    def check_excessive_skips(
        self,
        recent_telemetry: list[dict[str, Any]],
        max_skips: int = 5,
    ) -> CheckResult:
        skipped = sum(
            1 for r in recent_telemetry
            if r.get("events_processed", 0) == 0 and r.get("runtime_errors", 0) > 0
        )
        if skipped > max_skips:
            return CheckResult(
                check_name="excessive_skips",
                status=HealthStatus.CRITICAL,
                message=f"{skipped} skipped cycles in recent telemetry (limit {max_skips})",
                details={"skipped_cycles": skipped, "max_skips": max_skips},
            )
        if skipped > 0:
            return CheckResult(
                check_name="excessive_skips",
                status=HealthStatus.DEGRADED,
                message=f"{skipped} skipped cycles",
                details={"skipped_cycles": skipped},
            )
        return CheckResult(
            check_name="excessive_skips",
            status=HealthStatus.HEALTHY,
            message="No skipped cycles",
        )

    def run_all(
        self,
        equity: float,
        initial_capital: float,
        guard_mode: Any,
        crash_mode: Any,
        open_trades: list[Any],
        all_trades: list[Any],
        engine: Any,
        symbols: list[str],
        recent_telemetry: list[dict[str, Any]],
    ) -> list[CheckResult]:
        results: list[CheckResult] = [
            self.check_process_alive(),
            self.check_equity_sanity(equity, initial_capital),
            self.check_capital_guard_mode(guard_mode),
            self.check_crash_mode(crash_mode),
            self.check_open_positions(open_trades),
            self.check_negative_position_sizes(open_trades + all_trades),
            self.check_trade_consistency(all_trades),
            self.check_missing_price_data(engine, symbols),
            self.check_repeated_cycles(recent_telemetry),
            self.check_excessive_skips(recent_telemetry),
        ]
        return results

    @staticmethod
    def overall_status(results: list[CheckResult]) -> HealthStatus:
        if any(r.status == HealthStatus.CRITICAL for r in results):
            return HealthStatus.CRITICAL
        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
