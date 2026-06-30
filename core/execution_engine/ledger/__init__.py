"""Execution Engine immutable ledger domain."""

from core.execution_engine.ledger.types import LedgerRecordType

__all__ = ["ExecutionLedger", "LedgerRecordType"]


def __getattr__(name):
    if name == "ExecutionLedger":
        from core.execution_engine.ledger.ledger import ExecutionLedger

        return ExecutionLedger
    raise AttributeError(name)
