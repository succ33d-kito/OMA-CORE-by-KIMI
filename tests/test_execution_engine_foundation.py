"""Sprint 15A architecture tests for the Execution Engine foundation."""

from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path
import ast

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "core" / "execution_engine"


def test_execution_engine_package_structure_exists():
    expected_packages = [
        ENGINE_ROOT,
        ENGINE_ROOT / "engine",
        ENGINE_ROOT / "portfolio",
        ENGINE_ROOT / "positions",
        ENGINE_ROOT / "orders",
        ENGINE_ROOT / "ledger",
        ENGINE_ROOT / "metrics",
        ENGINE_ROOT / "schemas",
        ENGINE_ROOT / "config",
        ENGINE_ROOT / "exceptions",
        ENGINE_ROOT / "utils",
        ENGINE_ROOT / "tests",
    ]

    for package in expected_packages:
        assert package.is_dir(), f"Missing package directory: {package}"
        assert (package / "__init__.py").is_file(), f"Missing package initializer: {package / '__init__.py'}"


def test_execution_engine_public_foundation_imports_are_available():
    from core.execution_engine.config import DEFAULT_EXECUTION_MODE, ExecutionMode
    from core.execution_engine.engine import ExecutionEngine
    from core.execution_engine.exceptions import (
        ConfigurationError,
        ExecutionError,
        LedgerError,
        OrderError,
        PortfolioError,
        PositionError,
    )
    from core.execution_engine.ledger import LedgerRecordType
    from core.execution_engine.orders import OrderStatus
    from core.execution_engine.positions import PositionStatus
    from core.execution_engine.schemas import (
        ExecutionLedgerRecord,
        ExecutionOrder,
        ExecutionPortfolio,
        ExecutionPosition,
        ExecutionReport,
        ExecutionRequest,
        ExecutionResult,
        ExecutionSummary,
    )

    assert DEFAULT_EXECUTION_MODE is ExecutionMode.SIMULATION
    assert ExecutionEngine.__name__ == "ExecutionEngine"
    assert issubclass(OrderError, ExecutionError)
    assert issubclass(PortfolioError, ExecutionError)
    assert issubclass(PositionError, ExecutionError)
    assert issubclass(LedgerError, ExecutionError)
    assert issubclass(ConfigurationError, ExecutionError)
    assert OrderStatus.NEW.value == "NEW"
    assert PositionStatus.OPEN.value == "OPEN"
    assert LedgerRecordType.ENGINE_EVENT.value == "ENGINE_EVENT"

    for schema in (
        ExecutionLedgerRecord,
        ExecutionOrder,
        ExecutionPortfolio,
        ExecutionPosition,
        ExecutionReport,
        ExecutionRequest,
        ExecutionResult,
        ExecutionSummary,
    ):
        assert is_dataclass(schema)


def test_sprint_15a_structural_objects_are_immutable():
    from core.execution_engine.config import ExecutionMode
    from core.execution_engine.orders import OrderStatus
    from core.execution_engine.schemas import ExecutionOrder, ExecutionRequest

    request = ExecutionRequest(
        execution_request_id="req-1",
        execution_signal_id="sig-1",
        requested_action="record-approved-intent",
        execution_mode=ExecutionMode.SIMULATION,
        created_at="2026-06-29T00:00:00Z",
    )
    order = ExecutionOrder(
        execution_order_id="order-1",
        execution_request_id="req-1",
        order_state=OrderStatus.NEW,
        created_at="2026-06-29T00:00:00Z",
    )

    with pytest.raises(FrozenInstanceError):
        request.requested_action = "mutated"
    with pytest.raises(FrozenInstanceError):
        order.order_state = OrderStatus.FILLED


def test_sprint_15a_contains_no_forbidden_dependencies_or_placeholders():
    forbidden_roots = {
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
    forbidden_tokens = ("pass", "TODO", "TradingView", "broker_order", "Broker")

    assert ENGINE_ROOT.is_dir()
    for path in ENGINE_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
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
                assert imported not in forbidden_roots
                assert not any(imported.startswith(root + ".") for root in forbidden_roots)
