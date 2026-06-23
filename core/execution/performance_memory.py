"""OSIRIS Performance Memory — Trade attribution, agent track records, feedback loop
Records every trade with its Council decision and agent opinions.
Enables future agent weighting based on historical accuracy.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from statistics import mean, stdev
from collections import defaultdict

from core.schemas.trade_schema import Trade
from core.memory import MemoryStore


class PerformanceMemory:
    def __init__(self, memory_store: Optional[MemoryStore] = None):
        self.memory = memory_store or MemoryStore()
        self._trades: List[Trade] = []
        self._agent_records: Dict[str, List[dict]] = defaultdict(list)
        self._signal_records: Dict[str, List[dict]] = defaultdict(list)

    def record_trade(self, trade: Trade) -> None:
        self._trades.append(trade)
        self.memory.long_term.store(
            f"trade:{trade.signal.event_id}",
            trade.to_dict(),
            tags=["trade", trade.signal.asset, trade.signal.direction.value, trade.status.value],
        )

    def record_opinion_outcome(
        self,
        agent_name: str,
        opinion: dict,
        trade_result: float,
        correct: bool,
    ) -> None:
        record = {
            "agent_name": agent_name,
            "event_id": opinion.get("event_id", "unknown"),
            "recommendation": opinion.get("recommendation", "unknown"),
            "confidence": opinion.get("confidence", 0.5),
            "trade_result_pct": trade_result,
            "correct": correct,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._agent_records[agent_name].append(record)
        self.memory.long_term.store(
            f"agent_record:{agent_name}:{opinion.get('event_id', 'unknown')}",
            record,
            tags=["agent_record", agent_name, "correct" if correct else "incorrect"],
        )

    def get_agent_accuracy(self, agent_name: str, min_records: int = 3) -> float:
        records = self._agent_records.get(agent_name, [])
        if len(records) < min_records:
            return 0.5
        correct = sum(1 for r in records if r["correct"])
        return correct / len(records)

    def get_all_agent_accuracies(self) -> Dict[str, float]:
        return {
            name: self.get_agent_accuracy(name)
            for name in self._agent_records
        }

    def get_agent_confidence_calibration(self, agent_name: str) -> Dict[str, float]:
        records = self._agent_records.get(agent_name, [])
        if len(records) < 5:
            return {"bias": 0.0, "overconfidence": False, "underconfidence": False}

        avg_confidence = mean(r["confidence"] for r in records)
        actual_accuracy = self.get_agent_accuracy(agent_name)

        bias = avg_confidence - actual_accuracy
        return {
            "avg_confidence": round(avg_confidence, 3),
            "actual_accuracy": round(actual_accuracy, 3),
            "bias": round(bias, 3),
            "overconfidence": bias > 0.1,
            "underconfidence": bias < -0.1,
        }

    def get_performance_by_asset(self) -> Dict[str, float]:
        by_asset = defaultdict(list)
        for trade in self._trades:
            if trade.pnl_percent is not None:
                by_asset[trade.signal.asset].append(trade.pnl_percent)
        return {
            asset: round(mean(pnls), 2)
            for asset, pnls in by_asset.items()
        }

    def get_performance_by_direction(self) -> Dict[str, float]:
        long_pnls = [t.pnl_percent for t in self._trades if t.pnl_percent is not None and t.signal.direction.value == "long"]
        short_pnls = [t.pnl_percent for t in self._trades if t.pnl_percent is not None and t.signal.direction.value == "short"]
        return {
            "long_avg_pnl": round(mean(long_pnls), 2) if long_pnls else 0,
            "short_avg_pnl": round(mean(short_pnls), 2) if short_pnls else 0,
            "long_count": len(long_pnls),
            "short_count": len(short_pnls),
        }

    def get_recommendation_success_rate(self) -> Dict[str, float]:
        by_rec = defaultdict(list)
        for agent_name, records in self._agent_records.items():
            for r in records:
                by_rec[r["recommendation"]].append(r["correct"])
        return {
            rec: round(sum(results) / len(results) * 100, 1)
            for rec, results in by_rec.items()
        }

    def get_learning_summary(self) -> Dict[str, Any]:
        return {
            "total_trades_recorded": len(self._trades),
            "total_agent_records": sum(len(v) for v in self._agent_records.values()),
            "agent_accuracies": self.get_all_agent_accuracies(),
            "performance_by_asset": self.get_performance_by_asset(),
            "performance_by_direction": self.get_performance_by_direction(),
            "recommendation_success": self.get_recommendation_success_rate(),
            "calibration": {
                name: self.get_agent_confidence_calibration(name)
                for name in self._agent_records
            },
        }
