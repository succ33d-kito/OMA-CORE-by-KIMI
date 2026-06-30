"""Append-only execution ledger owned by the internal Execution Engine."""

from dataclasses import dataclass

from core.execution_engine.ledger.types import LedgerRecordType
from core.execution_engine.orders import OrderStatus
from core.execution_engine.exceptions import OrderError
from core.execution_engine.schemas.execution import ExecutionLedgerRecord, ExecutionOrder, ExecutionRequest


@dataclass(frozen=True, slots=True)
class ExecutionLedger:
    """Immutable append-only ledger for Sprint 15C order history."""

    records: tuple[ExecutionLedgerRecord, ...] = ()

    def create_order_with_record(self, execution_request: ExecutionRequest):
        """Create an internal order and its initial ledger record."""

        execution_order_id = f"order:{execution_request.execution_request_id}"
        order_trace = execution_request.upstream_trace + (
            f"execution_order_id:{execution_order_id}",
        )
        order = ExecutionOrder(
            execution_order_id=execution_order_id,
            execution_request_id=execution_request.execution_request_id,
            order_state=OrderStatus.NEW,
            created_at=execution_request.created_at,
            upstream_trace=order_trace,
        )
        record = self._build_record(
            order=order,
            execution_request=execution_request,
            previous_state="CREATED",
            next_state=OrderStatus.NEW.value,
            timestamp=execution_request.created_at,
        )
        return order, record

    def transition_order(
        self,
        order: ExecutionOrder,
        next_state: OrderStatus,
        *,
        timestamp: str,
    ):
        """Create a new order state and ledger event for an allowed transition."""

        if not self._transition_allowed(order.order_state, next_state):
            raise OrderError(
                f"Invalid order transition: {order.order_state.value}->{next_state.value}"
            )
        next_order = ExecutionOrder(
            execution_order_id=order.execution_order_id,
            execution_request_id=order.execution_request_id,
            order_state=next_state,
            created_at=order.created_at,
            upstream_trace=order.upstream_trace,
        )
        record = self._build_record_from_order(
            order=order,
            previous_state=order.order_state.value,
            next_state=next_state.value,
            timestamp=timestamp,
        )
        return next_order, record

    def append(self, record: ExecutionLedgerRecord):
        """Return a new ledger with record appended; never mutate history."""

        return ExecutionLedger(records=self.records + (record,))

    def reconstruct_order_history(self, execution_order_id: str):
        """Reconstruct deterministic order history from immutable records."""

        return tuple(
            record.state_transition
            for record in self.records
            if record.execution_order_id == execution_order_id
        )

    def _build_record(
        self,
        *,
        order: ExecutionOrder,
        execution_request: ExecutionRequest,
        previous_state: str,
        next_state: str,
        timestamp: str,
    ):
        sequence = self._next_sequence(order.execution_order_id)
        ledger_record_id = f"ledger:{order.execution_order_id}:{sequence:04d}"
        trace_values = self._trace_values(order.upstream_trace)
        return ExecutionLedgerRecord(
            execution_ledger_record_id=ledger_record_id,
            ledger_record_id=ledger_record_id,
            record_type=LedgerRecordType.ORDER_EVENT,
            created_at=timestamp,
            timestamp=timestamp,
            source_object_id=order.execution_order_id,
            execution_request_id=execution_request.execution_request_id,
            execution_order_id=order.execution_order_id,
            execution_signal_id=execution_request.execution_signal_id,
            decision_id=trace_values.get("decision_id", "missing:decision_id"),
            approval_id=trace_values.get("approval_id", "missing:approval_id"),
            state_transition=f"{previous_state}->{next_state}",
            upstream_trace=order.upstream_trace + (f"ledger_record_id:{ledger_record_id}",),
        )

    def _build_record_from_order(
        self,
        *,
        order: ExecutionOrder,
        previous_state: str,
        next_state: str,
        timestamp: str,
    ):
        sequence = self._next_sequence(order.execution_order_id)
        ledger_record_id = f"ledger:{order.execution_order_id}:{sequence:04d}"
        trace_values = self._trace_values(order.upstream_trace)
        return ExecutionLedgerRecord(
            execution_ledger_record_id=ledger_record_id,
            ledger_record_id=ledger_record_id,
            record_type=LedgerRecordType.ORDER_EVENT,
            created_at=timestamp,
            timestamp=timestamp,
            source_object_id=order.execution_order_id,
            execution_request_id=order.execution_request_id,
            execution_order_id=order.execution_order_id,
            execution_signal_id=trace_values.get(
                "execution_signal_id", "missing:execution_signal_id"
            ),
            decision_id=trace_values.get("decision_id", "missing:decision_id"),
            approval_id=trace_values.get("approval_id", "missing:approval_id"),
            state_transition=f"{previous_state}->{next_state}",
            upstream_trace=order.upstream_trace + (f"ledger_record_id:{ledger_record_id}",),
        )

    def _next_sequence(self, execution_order_id: str):
        return 1 + sum(
            1 for record in self.records if record.execution_order_id == execution_order_id
        )

    def _transition_allowed(self, current_state: OrderStatus, next_state: OrderStatus):
        allowed = {
            OrderStatus.NEW: {OrderStatus.PENDING},
            OrderStatus.PENDING: {
                OrderStatus.FILLED,
                OrderStatus.PARTIAL,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
                OrderStatus.EXPIRED,
            },
            OrderStatus.PARTIAL: {
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.EXPIRED,
            },
        }
        return next_state in allowed.get(current_state, set())

    def _trace_values(self, upstream_trace: tuple[str, ...]):
        values = {}
        for item in upstream_trace:
            key, separator, value = item.partition(":")
            if separator:
                values[key] = value
        return values
