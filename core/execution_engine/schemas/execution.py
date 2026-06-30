"""Structural objects owned by the internal Execution Engine.

These dataclasses are frozen to preserve Sprint 15A immutability boundaries.
They contain no execution behavior.
"""

from dataclasses import dataclass

from core.execution_engine.config import ExecutionMode
from core.execution_engine.ledger.types import LedgerRecordType
from core.execution_engine.orders import OrderStatus
from core.execution_engine.positions import PositionStatus


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Engine-owned request derived from a canonical ExecutionSignal."""

    execution_request_id: str
    execution_signal_id: str
    requested_action: str
    execution_mode: ExecutionMode
    created_at: str
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionOrder:
    """Engine-owned internal order structure."""

    execution_order_id: str
    execution_request_id: str
    order_state: OrderStatus
    created_at: str
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionPosition:
    """Engine-owned virtual position structure."""

    execution_position_id: str
    execution_order_id: str
    position_state: PositionStatus
    opened_at: str
    position_id: str | None = None
    execution_request_id: str | None = None
    execution_signal_id: str | None = None
    decision_id: str | None = None
    approval_id: str | None = None
    ledger_record_id: str | None = None
    state_version: str | None = None
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionPortfolio:
    """Engine-owned virtual portfolio snapshot structure."""

    portfolio_id: str
    snapshot_time: str
    execution_mode: ExecutionMode
    ledger_reference: str
    portfolio_snapshot_id: str | None = None
    state_version: str | None = None
    position_ids: tuple[str, ...] = ()
    exposure_count: int = 0
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionLedgerRecord:
    """Append-only execution history record structure."""

    execution_ledger_record_id: str
    record_type: LedgerRecordType
    created_at: str
    source_object_id: str
    ledger_record_id: str | None = None
    timestamp: str | None = None
    execution_request_id: str | None = None
    execution_order_id: str | None = None
    execution_signal_id: str | None = None
    decision_id: str | None = None
    approval_id: str | None = None
    state_transition: str | None = None
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Canonical pipeline boundary object produced by the Execution Engine."""

    execution_result_id: str
    execution_signal_id: str
    result_state: str
    created_at: str
    ledger_reference: str
    execution_request_id: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.SIMULATION
    error_code: str | None = None
    error_message: str | None = None
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionSummary:
    """Structural summary object for future Engine evidence reports."""

    summary_id: str
    created_at: str
    execution_mode: ExecutionMode
    upstream_trace: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Structural report object for future Engine evidence packages."""

    report_id: str
    created_at: str
    summary_id: str
    upstream_trace: tuple[str, ...] = ()
