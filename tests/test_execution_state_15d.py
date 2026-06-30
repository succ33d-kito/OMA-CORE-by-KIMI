"""Sprint 15D certification tests for deterministic Execution State."""

import ast
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "core" / "execution_engine"

VALID_SIGNAL = {
    "execution_signal_id": "sig-state-001",
    "approval_id": "approval-state-001",
    "decision_id": "decision-state-001",
    "intended_action": "CERTIFY_EXECUTION_STATE",
    "created_at": "2026-06-30T01:00:00Z",
    "event_id": "event-state-001",
    "opportunity_id": "opportunity-state-001",
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
    "profit_factor",
    "sharpe",
)


def _ledger_with_filled_order():
    from core.execution_engine.engine import ExecutionEngine
    from core.execution_engine.ledger import ExecutionLedger
    from core.execution_engine.orders import OrderStatus

    request = ExecutionEngine().create_execution_request(dict(VALID_SIGNAL))
    ledger = ExecutionLedger()
    order, created = ledger.create_order_with_record(request)
    ledger = ledger.append(created)
    pending_order, pending = ledger.transition_order(
        order,
        OrderStatus.PENDING,
        timestamp="2026-06-30T01:01:00Z",
    )
    ledger = ledger.append(pending)
    filled_order, filled = ledger.transition_order(
        pending_order,
        OrderStatus.FILLED,
        timestamp="2026-06-30T01:02:00Z",
    )
    ledger = ledger.append(filled)
    return ledger, filled_order


def test_layer_1_architecture_integrity_state_remains_isolated():
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


def test_layer_1_state_objects_are_engine_owned_and_immutable():
    from core.execution_engine.schemas import ExecutionPosition, ExecutionPortfolio
    from core.execution_engine.state import ExecutionState

    assert is_dataclass(ExecutionState)
    assert is_dataclass(ExecutionPosition)
    assert is_dataclass(ExecutionPortfolio)

    ledger, _ = _ledger_with_filled_order()
    state = ExecutionState.reconstruct(ledger.records)

    with pytest.raises(FrozenInstanceError):
        state.state_version = "mutated"
    with pytest.raises(FrozenInstanceError):
        state.positions[0].position_state = "mutated"
    with pytest.raises(FrozenInstanceError):
        state.portfolio_snapshot.portfolio_id = "mutated"


def test_layer_2_ledger_records_reconstruct_execution_state_position_and_snapshot():
    from core.execution_engine.positions import PositionStatus
    from core.execution_engine.state import ExecutionState

    ledger, order = _ledger_with_filled_order()
    state = ExecutionState.reconstruct(ledger.records)

    assert state.execution_state_id == "state:ledger:order:request:sig-state-001:0003"
    assert state.state_version == "3"
    assert state.timestamp == "2026-06-30T01:02:00Z"
    assert state.ledger_record_ids == (
        "ledger:order:request:sig-state-001:0001",
        "ledger:order:request:sig-state-001:0002",
        "ledger:order:request:sig-state-001:0003",
    )
    assert len(state.positions) == 1

    position = state.positions[0]
    assert position.execution_position_id == "position:order:request:sig-state-001"
    assert position.position_id == position.execution_position_id
    assert position.execution_order_id == order.execution_order_id
    assert position.position_state is PositionStatus.OPEN
    assert position.opened_at == "2026-06-30T01:02:00Z"
    assert position.decision_id == "decision-state-001"
    assert position.approval_id == "approval-state-001"
    assert position.execution_signal_id == "sig-state-001"
    assert position.execution_request_id == "request:sig-state-001"
    assert position.ledger_record_id == "ledger:order:request:sig-state-001:0003"

    snapshot = state.portfolio_snapshot
    assert snapshot.portfolio_id == "portfolio:snapshot:3"
    assert snapshot.portfolio_snapshot_id == snapshot.portfolio_id
    assert snapshot.snapshot_time == state.timestamp
    assert snapshot.ledger_reference == "ledger:order:request:sig-state-001:0003"
    assert snapshot.state_version == state.state_version
    assert snapshot.position_ids == (position.execution_position_id,)
    assert snapshot.exposure_count == 1


def test_layer_2_identical_ledger_reconstructs_identical_state():
    from core.execution_engine.state import ExecutionState

    first_ledger, _ = _ledger_with_filled_order()
    second_ledger, _ = _ledger_with_filled_order()

    assert ExecutionState.reconstruct(first_ledger.records) == ExecutionState.reconstruct(second_ledger.records)


def test_layer_3_snapshot_is_reproducible_and_exposure_consistent():
    from core.execution_engine.state import ExecutionState

    ledger, _ = _ledger_with_filled_order()
    state = ExecutionState.reconstruct(ledger.records)
    snapshot = state.portfolio_snapshot

    assert snapshot.position_ids == tuple(position.execution_position_id for position in state.positions)
    assert snapshot.exposure_count == len(state.positions)
    assert snapshot.upstream_trace[-1] == f"portfolio_snapshot_id:{snapshot.portfolio_id}"


def test_layer_3_position_lifecycle_is_deterministic_from_ledger():
    from core.execution_engine.positions import PositionStatus
    from core.execution_engine.state import ExecutionState

    ledger, _ = _ledger_with_filled_order()
    state = ExecutionState.reconstruct(ledger.records)

    lifecycle = state.position_lifecycle("position:order:request:sig-state-001")

    assert lifecycle == (PositionStatus.OPEN,)
    assert state.validate_consistency() is True


def test_layer_4_corrupted_ledger_sequence_is_rejected_deterministically():
    from core.execution_engine.exceptions import LedgerError
    from core.execution_engine.state import ExecutionState

    ledger, _ = _ledger_with_filled_order()
    corrupted = (ledger.records[0], ledger.records[2])

    with pytest.raises(LedgerError) as excinfo:
        ExecutionState.reconstruct(corrupted)

    assert str(excinfo.value) == "Corrupted ledger sequence for order:request:sig-state-001"


def test_layer_4_empty_ledger_history_is_rejected_deterministically():
    from core.execution_engine.exceptions import LedgerError
    from core.execution_engine.state import ExecutionState

    with pytest.raises(LedgerError) as excinfo:
        ExecutionState.reconstruct(())

    assert str(excinfo.value) == "ExecutionState requires at least one ledger record"


def test_layer_4_invalid_state_reconstruction_is_rejected():
    from dataclasses import replace

    from core.execution_engine.exceptions import LedgerError
    from core.execution_engine.state import ExecutionState

    ledger, _ = _ledger_with_filled_order()
    invalid = replace(ledger.records[1], state_transition="FILLED->PENDING")

    with pytest.raises(LedgerError) as excinfo:
        ExecutionState.reconstruct((ledger.records[0], invalid, ledger.records[2]))

    assert str(excinfo.value) == "Invalid state transition in ledger: FILLED->PENDING"
