"""Execution Engine metrics domain.

Sprint 15A defines the package boundary only. Metric calculations begin in a
future sprint after execution evidence exists.
"""

METRIC_NAMES = (
    "Win Rate",
    "Profit Factor",
    "Expectancy",
    "Average Win",
    "Average Loss",
    "Sharpe",
    "Sortino",
    "Maximum Drawdown",
    "Recovery Factor",
)

__all__ = ["METRIC_NAMES"]
