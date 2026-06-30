"""Sprint 15C certification tests for immutable execution order ledger memory."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "core" / "execution_engine"

VALID_SIGNAL = {
    "execution_signal_id": "sig-ledger-001",
    "approval_id": "approval-ledger-001",
    "decision_id": "decision-ledger-001",
    "intended_action": "CERTIFY_LEDGER_MEMORY",
    "created_at": "2026-06-30T00:00:00Z",
    "event_id": "event-ledger-001",
    "opportunity_id": "opportunity-ledger-001",
}

FORBIDDEN_IMPORT_ROOTS = {
    "core.collectors",
    "core.council",
    "core.database",
    "core.engines",
    "core.event_bus",
    "core.scientific",
    "core.cli",
    "core.integration",
    "core.execution",
}

FORBIDDEN_TEXT = (
    "TradingView",
    "broker_order",
    "Broker",
    "paper_trading",
    "scientific_store",
    "sqlite3",
    "portfolio_value",
    "pnl",
)


def _request():
    from core.execution_engine.engine import ExecutionEngine

    return ExecutionEngine().create_execution_request(dict(VALID_SIGNAL))


def test_layer_1_architecture_integrity_order_ledger_remains_isolated():
    assert ENGINE_ROOT.is_dir()

    for path in ENGINE_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT:
            assert token not in source, f"Forbidden token {token!r} found in {path}"

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_names = [node.module or ""]
            else:
                continue

            for imported in imported_names:
                assert imported not in FORBIDDEN_IMPORT_ROOTS
                assert not any(imported.startswith(root + ".") for root in FORBIDDEN_IMPORT_ROOTS)


def test_layer_1_ownership_objects_are_engine_owned_and_immutable():
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.schemas import ExecutionLedgerRecord, ExecutionOrder

    assert is_dataclass(ExecutionOrder)
    assert is_dataclass(ExecutionLedgerRecord)
    assert is_dataclass(ExecutionLedger)

    order, record = ExecutionLedger().create_order_with_record(_request())

    with pytest.raises(FrozenInstanceError):
        order.order_state = "MUTATED"
    with pytest.raises(FrozenInstanceError):
        record.state_transition = "MUTATED"


def test_layer_2_execution_request_creates_order_and_initial_ledger_record():
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.ledger import LedgerRecordType
    from core.execution_engine.orders import OrderStatus

    request = _request()
    ledger = ExecutionLedger()
    order, record = ledger.create_order_with_record(request)

    assert order.execution_order_id == "order:request:sig-ledger-001"
    assert order.execution_request_id == request.execution_request_id
    assert order.order_state is OrderStatus.NEW
    assert order.created_at == request.created_at
    assert order.upstream_trace == (
        "event_id:event-ledger-001",
        "opportunity_id:opportunity-ledger-001",
        "decision_id:decision-ledger-001",
        "approval_id:approval-ledger-001",
        "execution_signal_id:sig-ledger-001",
        "execution_request_id:request:sig-ledger-001",
        "execution_order_id:order:request:sig-ledger-001",
    )

    assert record.ledger_record_id == "ledger:order:request:sig-ledger-001:0001"
    assert record.execution_ledger_record_id == record.ledger_record_id
    assert record.record_type is LedgerRecordType.ORDER_EVENT
    assert record.execution_order_id == order.execution_order_id
    assert record.execution_request_id == request.execution_request_id
    assert record.execution_signal_id == request.execution_signal_id
    assert record.decision_id == "decision-ledger-001"
    assert record.approval_id == "approval-ledger-001"
    assert record.timestamp == request.created_at
    assert record.state_transition == "CREATED->NEW"


def test_layer_2_append_only_transition_history_is_recorded_as_new_events():
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.orders import OrderStatus

    request = _request()
    ledger = ExecutionLedger()
    order, created = ledger.create_order_with_record(request)
    ledger = ledger.append(created)

    pending_order, pending_record = ledger.transition_order(
        order,
        OrderStatus.PENDING,
        timestamp="2026-06-30T00:01:00Z",
    )
    ledger = ledger.append(pending_record)

    filled_order, filled_record = ledger.transition_order(
        pending_order,
        OrderStatus.FILLED,
        timestamp="2026-06-30T00:02:00Z",
    )
    ledger = ledger.append(filled_record)

    assert order.order_state is OrderStatus.NEW
    assert pending_order.order_state is OrderStatus.PENDING
    assert filled_order.order_state is OrderStatus.FILLED
    assert [r.state_transition for r in ledger.records] == [
        "CREATED->NEW",
        "NEW->PENDING",
        "PENDING->FILLED",
    ]
    assert [r.ledger_record_id for r in ledger.records] == [
        "ledger:order:request:sig-ledger-001:0001",
        "ledger:order:request:sig-ledger-001:0002",
        "ledger:order:request:sig-ledger-001:0003",
    ]


def test_layer_3_ledger_is_append_only_and_records_cannot_be_deleted_or_modified():
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.orders import OrderStatus

    ledger = ExecutionLedger()
    order, created = ledger.create_order_with_record(_request())
    ledger = ledger.append(created)
    pending_order, pending_record = ledger.transition_order(
        order,
        OrderStatus.PENDING,
        timestamp="2026-06-30T00:01:00Z",
    )
    ledger = ledger.append(pending_record)

    with pytest.raises(FrozenInstanceError):
        ledger.records = ()
    with pytest.raises(AttributeError):
        ledger.records.pop()
    with pytest.raises(FrozenInstanceError):
        pending_record.timestamp = "mutated"

    assert len(ledger.records) == 2
    assert ledger.records[0] == created
    assert pending_order.order_state is OrderStatus.PENDING


def test_layer_3_history_reconstruction_is_deterministic_from_immutable_records():
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.orders import OrderStatus

    request = _request()
    ledger = ExecutionLedger()
    order, created = ledger.create_order_with_record(request)
    ledger = ledger.append(created)
    pending_order, pending_record = ledger.transition_order(
        order,
        OrderStatus.PENDING,
        timestamp="2026-06-30T00:01:00Z",
    )
    ledger = ledger.append(pending_record)
    filled_order, filled_record = ledger.transition_order(
        pending_order,
        OrderStatus.FILLED,
        timestamp="2026-06-30T00:02:00Z",
    )
    ledger = ledger.append(filled_record)

    first = ledger.reconstruct_order_history(filled_order.execution_order_id)
    second = ledger.reconstruct_order_history(filled_order.execution_order_id)

    assert first == second
    assert first == (
        "CREATED->NEW",
        "NEW->PENDING",
        "PENDING->FILLED",
    )


def test_layer_3_invalid_transition_is_rejected_without_mutating_history():
    from core.execution_engine.exceptions import OrderError
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.orders import OrderStatus

    ledger = ExecutionLedger()
    order, created = ledger.create_order_with_record(_request())
    ledger = ledger.append(created)

    with pytest.raises(OrderError):
        ledger.transition_order(order, OrderStatus.FILLED, timestamp="2026-06-30T00:03:00Z")

    assert ledger.reconstruct_order_history(order.execution_order_id) == ("CREATED->NEW",)
