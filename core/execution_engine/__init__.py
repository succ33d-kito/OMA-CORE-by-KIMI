"""Internal Execution Engine foundation for O.M.A.-C.O.R.E. Sprint 15A.

This subsystem owns future internal execution structure only. Sprint 15A
contains no execution behavior.
"""

from core.execution_engine.config import DEFAULT_EXECUTION_MODE, ExecutionEngineConfig, ExecutionMode
from core.execution_engine.engine import ExecutionEngine

__all__ = [
    "DEFAULT_EXECUTION_MODE",
    "ExecutionEngine",
    "ExecutionEngineConfig",
    "ExecutionMode",
]
