"""Deterministic Execution State reconstructed from immutable ledger records."""

from dataclasses import dataclass

from core.execution_engine.config import DEFAULT_EXECUTION_MODE
from core.execution_engine.exceptions import LedgerError
from core.execution_engine.positions import PositionStatus
from core.execution_engine.schemas import ExecutionLedgerRecord, ExecutionPortfolio, ExecutionPosition


@dataclass(frozen=True, slots=True)
class ExecutionState:
    """Authoritative internal operational state of the Execution Engine."""

    execution_state_id: str
    timestamp: str
    state_version: str
    ledger_record_ids: tuple[str, ...]
    positions: tuple[ExecutionPosition, ...]
    portfolio_snapshot: ExecutionPortfolio
    upstream_trace: tuple[str, ...] = ()

    @classmethod
    def reconstruct(cls, ledger_records: tuple[ExecutionLedgerRecord, ...]):
        """Reconstruct deterministic state exclusively from immutable ledger records."""

        if not ledger_records:
            raise LedgerError("ExecutionState requires at least one ledger record")

        current_order_states: dict[str, str] = {}
        positions: dict[str, ExecutionPosition] = {}
        ledger_record_ids = tuple(
            record.ledger_record_id or record.execution_ledger_record_id
            for record in ledger_records
        )

        for record in ledger_records:
            cls._validate_record(record)
            previous_state, next_state = cls._parse_transition(record.state_transition or "")
            order_id = record.execution_order_id or "missing:execution_order_id"
            current_state = current_order_states.get(order_id)

            if current_state is None:
                if previous_state != "CREATED" or next_state != "NEW":
                    raise LedgerError(f"Corrupted ledger sequence for {order_id}")
            elif current_state != previous_state:
                if not cls._transition_allowed(previous_state, next_state):
                    raise LedgerError(
                        f"Invalid state transition in ledger: {previous_state}->{next_state}"
                    )
                raise LedgerError(f"Corrupted ledger sequence for {order_id}")
            elif not cls._transition_allowed(previous_state, next_state):
                raise LedgerError(
                    f"Invalid state transition in ledger: {previous_state}->{next_state}"
                )

            current_order_states[order_id] = next_state
            if next_state == "FILLED":
                position_id = f"position:{order_id}"
                positions[position_id] = cls._position_from_record(
                    position_id=position_id,
                    record=record,
                    state_version=str(len(ledger_record_ids)),
                )

        last_record = ledger_records[-1]
        state_version = str(len(ledger_records))
        sorted_positions = tuple(positions[key] for key in sorted(positions))
        snapshot = cls._snapshot_from_records(
            state_version=state_version,
            timestamp=last_record.timestamp or last_record.created_at,
            latest_record=last_record,
            positions=sorted_positions,
        )
        return cls(
            execution_state_id=f"state:{last_record.ledger_record_id}",
            timestamp=last_record.timestamp or last_record.created_at,
            state_version=state_version,
            ledger_record_ids=ledger_record_ids,
            positions=sorted_positions,
            portfolio_snapshot=snapshot,
            upstream_trace=last_record.upstream_trace
            + (
                f"state_version:{state_version}",
                f"portfolio_snapshot_id:{snapshot.portfolio_id}",
            ),
        )

    def validate_consistency(self):
        """Validate internal state and snapshot consistency."""

        position_ids = tuple(position.execution_position_id for position in self.positions)
        if self.portfolio_snapshot.position_ids != position_ids:
            raise LedgerError("Portfolio snapshot position_ids do not match state positions")
        if self.portfolio_snapshot.exposure_count != len(self.positions):
            raise LedgerError("Portfolio snapshot exposure count does not match state positions")
        if self.portfolio_snapshot.state_version != self.state_version:
            raise LedgerError("Portfolio snapshot state version does not match ExecutionState")
        return True

    def position_lifecycle(self, position_id: str):
        """Return deterministic lifecycle states for one reconstructed position."""

        return tuple(
            position.position_state
            for position in self.positions
            if position.execution_position_id == position_id
        )

    @classmethod
    def _position_from_record(
        cls,
        *,
        position_id: str,
        record: ExecutionLedgerRecord,
        state_version: str,
    ):
        trace = record.upstream_trace + (
            f"position_id:{position_id}",
            f"state_version:{state_version}",
        )
        return ExecutionPosition(
            execution_position_id=position_id,
            position_id=position_id,
            execution_order_id=record.execution_order_id or "missing:execution_order_id",
            execution_request_id=record.execution_request_id,
            execution_signal_id=record.execution_signal_id,
            decision_id=record.decision_id,
            approval_id=record.approval_id,
            ledger_record_id=record.ledger_record_id,
            state_version=state_version,
            position_state=PositionStatus.OPEN,
            opened_at=record.timestamp or record.created_at,
            upstream_trace=trace,
        )

    @classmethod
    def _snapshot_from_records(
        cls,
        *,
        state_version: str,
        timestamp: str,
        latest_record: ExecutionLedgerRecord,
        positions: tuple[ExecutionPosition, ...],
    ):
        portfolio_id = f"portfolio:snapshot:{state_version}"
        position_ids = tuple(position.execution_position_id for position in positions)
        return ExecutionPortfolio(
            portfolio_id=portfolio_id,
            portfolio_snapshot_id=portfolio_id,
            snapshot_time=timestamp,
            execution_mode=DEFAULT_EXECUTION_MODE,
            ledger_reference=latest_record.ledger_record_id or latest_record.execution_ledger_record_id,
            state_version=state_version,
            position_ids=position_ids,
            exposure_count=len(position_ids),
            upstream_trace=latest_record.upstream_trace
            + (
                f"state_version:{state_version}",
                f"portfolio_snapshot_id:{portfolio_id}",
            ),
        )

    @classmethod
    def _validate_record(cls, record: ExecutionLedgerRecord):
        required = (
            record.decision_id,
            record.approval_id,
            record.execution_signal_id,
            record.execution_request_id,
            record.execution_order_id,
            record.ledger_record_id,
            record.timestamp,
            record.state_transition,
        )
        if not all(required):
            raise LedgerError("ExecutionState cannot reconstruct from incomplete ledger record")

    @classmethod
    def _parse_transition(cls, state_transition: str):
        previous_state, separator, next_state = state_transition.partition("->")
        if not separator or not previous_state or not next_state:
            raise LedgerError(f"Invalid state transition in ledger: {state_transition}")
        return previous_state, next_state

    @classmethod
    def _transition_allowed(cls, previous_state: str, next_state: str):
        allowed = {
            "CREATED": {"NEW"},
            "NEW": {"PENDING"},
            "PENDING": {"FILLED", "PARTIAL", "CANCELLED", "REJECTED", "EXPIRED"},
            "PARTIAL": {"FILLED", "CANCELLED", "EXPIRED"},
        }
        return next_state in allowed.get(previous_state, set())
