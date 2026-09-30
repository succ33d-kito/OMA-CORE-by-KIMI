"""Prospective 24h reference forecast and exact-horizon label resolver."""
from datetime import datetime, timedelta
from hashlib import sha256
from core.market_mechanics.regime import classify_regime

MODEL = "constant-probability-0.5-v1"
TARGET = "close_at_anchor_plus_24h_strictly_above_anchor_close"


def issue_reference(journal, state, event_id):
    anchor = datetime.fromisoformat(state.last_bar_closed_at)
    issued = datetime.fromisoformat(state.as_of)
    end = anchor + timedelta(hours=24)
    if issued >= end:
        raise ValueError("forecast horizon has already ended")
    key = sha256(f"{MODEL}:{state.source_id}:{state.symbol}:{anchor.isoformat()}".encode()).hexdigest()
    existing = journal.get(key)
    if existing:
        if existing["context"]["anchor_price"] != state.last_close:
            raise ValueError("anchor price was revised; cannot overwrite forecast")
        return key
    regime = classify_regime(state)
    journal.record(forecast_id=key, target=TARGET, probability=.5, issued_at=issued,
                   available_at=datetime.fromisoformat(state.observed_at), horizon_end=end,
                   model_version=MODEL, regime_id=regime.regime_id,
                   regime_label=f"{regime.structure}:{regime.volatility}",
                   context=dict(symbol=state.symbol, source_id=state.source_id, event_id=event_id,
                                market_state_id=state.state_id, anchor_price=state.last_close,
                                anchor_closed_at=anchor.isoformat(), timeframe_seconds=state.timeframe_seconds))
    return key


def resolve_from_market_state(journal, state):
    observed = datetime.fromisoformat(state.observed_at)
    closes = {datetime.fromisoformat(row[0])+timedelta(seconds=state.timeframe_seconds): row[4]
              for row in state.input_bars}
    count = 0
    for key, forecast in journal.forecasts(pending_only=True).items():
        c = forecast.get("context", {})
        if forecast["model_version"] != MODEL or forecast["target"] != TARGET:
            continue
        if c.get("symbol") != state.symbol or c.get("source_id") != state.source_id:
            continue
        end = datetime.fromisoformat(forecast["horizon_end"])
        if end > observed or end not in closes:
            continue
        journal.resolve(key, outcome=closes[end] > c["anchor_price"], observed_at=observed,
                        source_id=f"{state.source_id}:market_state:{state.state_id}:close:{end.isoformat()}")
        count += 1
    return count
