"""Ledger record type names for Engine-owned history records."""

from enum import Enum


class LedgerRecordType(Enum):
    """Allowed ledger record categories for Sprint 15A structure."""

    ENGINE_EVENT = "ENGINE_EVENT"
    REQUEST_EVENT = "REQUEST_EVENT"
    ORDER_EVENT = "ORDER_EVENT"
    POSITION_EVENT = "POSITION_EVENT"
    PORTFOLIO_EVENT = "PORTFOLIO_EVENT"
    RESULT_EVENT = "RESULT_EVENT"
