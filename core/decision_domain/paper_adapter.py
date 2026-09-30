"""Explicit bridge from legacy paper trades into the decision journal."""

from datetime import datetime, timezone
from uuid import uuid4
import json

from core.decision_domain.record import DecisionJournal, DecisionOutcome, DecisionRecord
from core.market_mechanics.regime import classify_regime


def record_paper_signal(journal: DecisionJournal, event, council_decision, signal, market_state=None) -> str:
    """Freeze the executable paper plan before execute_signal is called."""
    now = datetime.now(timezone.utc)
    decision_id = str(uuid4())
    missing = ["hypothesis_id", "validated_evidence_ids", "market_state_id"]
    regime = None
    if market_state is not None:
        if market_state.symbol != signal.asset or datetime.fromisoformat(market_state.as_of) > now:
            raise ValueError("market state does not match the decision asset/time")
        age = (now - datetime.fromisoformat(market_state.last_bar_closed_at)).total_seconds()
        if age > 2 * market_state.timeframe_seconds:
            raise ValueError("market state is stale at decision time")
        missing.remove("market_state_id")
        missing.extend(market_state.unknown_dimensions)
        regime = classify_regime(market_state)
        missing.extend(f"regime:{axis}" for axis in regime.unknown_axes)
        if regime.volatility == "unknown":
            missing.append("regime:volatility")
    record = DecisionRecord(
        decision_id=decision_id,
        event_id=event.id,
        hypothesis_id=None,
        decided_at=now,
        available_at=now,
        action=f"paper_{signal.direction.value}",
        alternative_actions=("no_action",),
        evidence_ids=(),
        source_ids=tuple(dict.fromkeys(filter(None, (event.source_id or event.source,
                         market_state.source_id if market_state else None)))),
        market_state_id=market_state.state_id if market_state else None,
        market_state_snapshot=json.dumps(market_state.to_dict(), sort_keys=True) if market_state else None,
        regime_snapshot=json.dumps(regime.to_dict(), sort_keys=True) if regime else None,
        expected_outcome=(f"{signal.asset} reaches {signal.take_profit} before {signal.stop_loss} "
                          f"within {signal.time_horizon_hours}h"),
        invalidation_condition=(f"{signal.asset} reaches stop {signal.stop_loss} "
                                f"or the {signal.time_horizon_hours}h horizon expires"),
        risk_constraints=(f"paper only; entry={signal.entry_price}; "
                          f"size_pct={signal.position_size_pct}; stop={signal.stop_loss}",),
        missing_information=tuple(missing),
        rationale=council_decision.rationale if council_decision else signal.rationale,
    )
    journal.record(record)
    # The ID travels with the signal into the Trade, including resumed positions.
    signal.metadata["decision_record_id"] = decision_id
    return decision_id


def observe_paper_trade(journal: DecisionJournal, trade) -> bool:
    """Append factual closure; do not assign decision quality from PnL."""
    decision_id = trade.signal.metadata.get("decision_record_id")
    if not decision_id:
        return False
    journal.observe(paper_trade_outcome(trade))
    return True


def paper_trade_outcome(trade) -> DecisionOutcome:
    decision_id = trade.signal.metadata["decision_record_id"]
    facts = (f"asset={trade.signal.asset}", f"exit_reason={trade.exit_reason.value}",
             f"exit_price={trade.exit_price}", f"pnl_percent={trade.pnl_percent}")
    return DecisionOutcome(decision_id, f"paper-close:{decision_id}", trade.exit_time, facts)


def observe_paper_block(journal: DecisionJournal, decision_id: str, reason: str) -> None:
    journal.observe(paper_block_outcome(decision_id, reason))


def paper_block_outcome(decision_id: str, reason: str) -> DecisionOutcome:
    return DecisionOutcome(decision_id, f"paper-block:{decision_id}",
                           datetime.now(timezone.utc), (f"paper_execution_block={reason}",))


def observe_canonical_outcome(journal: DecisionJournal, outcome) -> None:
    """Consume a real published Outcome; never synthesize ExecutionResult lineage."""
    if not outcome.publication_ready or outcome.lifecycle_state != "OUTCOME_PUBLISHED":
        raise ValueError("canonical outcome is not publication ready")
    created = [t.split(":", 1)[1] for t in outcome.timestamps if t.startswith("created_at:")]
    if len(created) != 1:
        raise ValueError("canonical outcome requires one creation timestamp")
    observed_at = datetime.fromisoformat(created[0].replace("Z", "+00:00"))
    journal.observe(DecisionOutcome(outcome.decision_id, outcome.outcome_id,
                                    observed_at, outcome.result_facts))
