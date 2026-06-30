"""Configuration objects for the internal Execution Engine."""

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(Enum):
    """Canonical execution modes defined by Integration Architecture V1.1."""

    SIMULATION = "SIMULATION"
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    LIVE = "LIVE"


DEFAULT_EXECUTION_MODE = ExecutionMode.SIMULATION


@dataclass(frozen=True, slots=True)
class ExecutionEngineConfig:
    """Structural configuration for the Execution Engine foundation."""

    mode: ExecutionMode = DEFAULT_EXECUTION_MODE
    ledger_enabled: bool = True
    metrics_enabled: bool = True
